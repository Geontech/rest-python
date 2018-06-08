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

For Development/Test environments there are scripts to automatically create a local environment and run the server. You will need to install the `virtualenv` python package before using the commands below.

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

## Testing

If you would like to test REST-Python changes in a functional domain, download Docker-CE and Docker Compose for your operating system.  The process takes 3 parts:

 1. Your locally-built instance of the webserver image
 2. Running the `tests/docker-compose.yml` stack with your webserver image
 3. Using `docker-compose exec` to start the tests script.

 > Note: Verify the Dockerfile version of the parent image (`FROM...`) and the compose file vs. the version of REDHAWK you want to test against.  You can export `REDHAWK_VERSION` set to that version prior to running `docker-compose` to simplify changing versions of the infrastructure.

The process is shown here:

```
cd tests
export TEST_IMAGE=test-webserver
docker-compose up -d --build
docker-compose exec -T rest \
    bash -l -c 'yum install -y rh.FileWriter rh.SigGen && ./test.sh'
```

If you make further changes and want to update the webserver image and container (the service is `rest` in the compose file), you can recreate the container without tearing down the entire compose by doing the following:

```
docker-compose stop rest
docker-compose up --build -d rest
```

You would then repeat the `exec` command from above.
