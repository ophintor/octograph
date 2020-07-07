Octograph
---------

Project forked and modified from https://github.com/stevenewey/octograph.

Python tool for downloading energy consumption data from the
`Octopus Energy API`_ and loading it into `InfluxDB`_.

In the process, Agile tariff metrics will be generated and stored for unit rates
and costs. Suitable for Octopus Agile tariffs.

Included is an example `Grafana`_ dashboard to visualise the captured data.

An example Docker Compose file is included for easily running InfluxDB and
Grafana.

.. image:: grafana-dashboard.png
   :width: 800

Installation
============

Tested on macOS with Docker for Mac and Python 3.6. A Python virtualenv is
recommended.

Install the Python requirements with ``pip``

.. code:: bash

    pip install -r app/requirements.txt


Usage
=====

Create a configuration file ``octograph.ini`` customised with your Octopus
API key, meter details and energy rate information. This file should be in the
working directory where you run the ``octopus_to_influxdb.py`` command, or
can be passed as an argument.

.. code:: bash

    python app/octopus_to_influxdb.py --help

By default, energy data for the previous day will be collected. Optional from
and to ranges may be specified to retrieve larger datasets. It is anticipated
that the script will be run daily by a cron job (see ``cronjob.sh``).

.. code:: bash

    docker-compose up -d  # start InfluxDB and Grafana in Docker
    python app/octopus_to_infuxdb.py --from-date=2018-10-20
    open http://localhost:3000

The default login credentials for Grafana are admin/admin, and you will be
prompted to set a new password on first login. You should then proceed to add
InfluxDB as a datasource with URL ``http://influxdb:8086`` and database
``energy`` if using the Docker version provided. The dashboard provided can
then be imported to review the data.


.. _Octopus Energy API: https://developer.octopus.energy/docs/api/
.. _Octopus Energy Go: https://octopus.energy/go/
.. _InfluxDB: https://www.influxdata.com/time-series-platform/influxdb/
.. _Grafana: https://grafana.com
