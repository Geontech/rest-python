# REDHAWK REST Python

## Description

Contains the REDHAWK python implementation of the generic [REST API](http://geontech.github.io/rest-python).

Please visit [the Wiki](https://github.com/Geontech/rest-python/wiki) for more detailed instructions on the changes made to this repository and how it can be used for development of external control interfaces, data bridges, and graphical user interfaces without having to install REDHAWK on the target system.

## REDHAWK Documentation

REDHAWK Website: [www.redhawksdr.org](http://www.redhawksdr.org)

## Copyrights

This work is protected by Copyright. Please refer to the [Copyright File](COPYRIGHT) for updated copyright information.

## License

REDHAWK REST Python is licensed under the GNU Lesser General Public License (LGPL).

## Running

For Development/Test environments there are scripts to automatically create a local environment and run the server.

    ./setup.sh install
    ./start.sh --port=<desired_port>

The tools above will create a virtual environment in the current directory.

For a more permanent solution, consult the `requirements.txt` and run the following command as a service:

     ./pyrest.py --port=<desired_port>

`supervisord` is a common tool for running commands as a service and a sample configuration snippet
can be found at `deploy/rest-python-supervisor.conf`.

Once running the REST Interface can be tested at `http://localhost:<desired_port>/rh/rest/domains`.

## Deploying Applications

You can either install your application in `apps` for REST-Python to serve them, or deploy them with a separate server (e.g., NodeJS).  REST-Python supports cross-domain responses to REST and Websocket requests to facilitate dual- or multi-server configurations to completely decouple the REDHAWK environment from the web application environment.  (See [Docker-REDHAWK's](http://github.com/GeonTech/docker-redhawk) `geontech/redhawk-webserver` image.)

