# REDHAWK REST Python

## Description

Contains the REDHAWK python implementation of the generic REST API.

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

