#!/usr/bin/env python

from configparser import ConfigParser
from urllib import parse

import click
import maya
import requests
from influxdb import InfluxDBClient


def retrieve_paginated_data(
        api_key, url, from_date, to_date, page=None
):
    args = {
        'period_from': from_date,
        'period_to': to_date,
    }
    if page:
        args['page'] = page
    response = requests.get(url, params=args, auth=(api_key, ''))
    response.raise_for_status()
    data = response.json()
    results = data.get('results', [])
    if data['next']:
        url_query = parse.urlparse(data['next']).query
        next_page = parse.parse_qs(url_query)['page'][0]
        results += retrieve_paginated_data(
            api_key, url, from_date, to_date, next_page
        )
    return results


def store_series(connection, series, metrics, rate_data):

    agile_data = rate_data.get('agile_unit_rates', [])
    agile_rates = {
        point['valid_to']: point['value_inc_vat']
        for point in agile_data
    }

    def fields_for_measurement(measurement):
        consumption = measurement['consumption']
        fields = {
            'consumption': consumption,
        }
        if agile_data:
            agile_standing_charge = rate_data['agile_standing_charge'] / 48
            agile_unit_rate = agile_rates.get(
                maya.parse(measurement['interval_end']).iso8601()
            )
            agile_cost = agile_unit_rate * consumption
            fields.update({
                'agile_rate': agile_unit_rate,
                'agile_cost': agile_cost,
                'agile_total_cost': agile_cost + agile_standing_charge,
            })
        return fields

    def tags_for_measurement(measurement):
        period = maya.parse(measurement['interval_end'])
        time = period.datetime().strftime('%H:%M')
        return {
            'time_of_day': time,
        }

    measurements = [
        {
            'measurement': series,
            'tags': tags_for_measurement(measurement),
            'time': measurement['interval_end'],
            'fields': fields_for_measurement(measurement),
        }
        for measurement in metrics
    ]
    connection.write_points(measurements)


@click.command()
@click.option(
    '--config-file',
    default="octograph.ini",
    type=click.Path(exists=True, dir_okay=True, readable=True),
)
@click.option('--from-date', default='yesterday midnight', type=click.STRING)
@click.option('--to-date', default='tomorrow midnight', type=click.STRING)

def cmd(config_file, from_date, to_date):

    config = ConfigParser()
    config.read(config_file)

    influx = InfluxDBClient(
        host=config.get('influxdb', 'host', fallback="localhost"),
        port=config.getint('influxdb', 'port', fallback=8086),
        username=config.get('influxdb', 'user', fallback=""),
        password=config.get('influxdb', 'password', fallback=""),
        database=config.get('influxdb', 'database', fallback="energy"),
    )

    api_key = config.get('octopus', 'api_key')
    if not api_key:
        raise click.ClickException('No Octopus API key set')

    e_mpan = config.get('electricity', 'mpan', fallback=None)
    e_serial = config.get('electricity', 'serial_number', fallback=None)
    if not e_mpan or not e_serial:
        raise click.ClickException('No electricity meter identifiers')
    e_url = 'https://api.octopus.energy/v1/electricity-meter-points/' \
            f'{e_mpan}/meters/{e_serial}/consumption/'
    agile_url = config.get('electricity', 'agile_rate_url', fallback=None)

    timezone = config.get('electricity', 'timezone', fallback=None)

    rate_data = {
        'electricity': {
            'agile_standing_charge': config.getfloat(
                'electricity', 'agile_standing_charge', fallback=0.0
            ),
            'agile_unit_rates': [],
        }
    }

    from_iso = maya.when(from_date, timezone=timezone).iso8601()
    to_iso = maya.when(to_date, timezone=timezone).iso8601()

    click.echo(
        f'Retrieving electricity data for {from_iso} until {to_iso}...',
    )
    e_consumption = retrieve_paginated_data(
        api_key, e_url, from_iso, to_iso
    )
    click.echo(f' {len(e_consumption)} readings.')
    click.echo(
        f'Retrieving Agile rates for {from_iso} until {to_iso}...',
    )
    rate_data['electricity']['agile_unit_rates'] = retrieve_paginated_data(
        api_key, agile_url, from_iso, to_iso
    )
    click.echo(f' {len(rate_data["electricity"]["agile_unit_rates"])} rates.')
    store_series(influx, 'electricity', e_consumption, rate_data['electricity'])



if __name__ == '__main__':
    cmd()
