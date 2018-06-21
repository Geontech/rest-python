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

### Using GitLab Runner Locally

You can run individual jobs defined in the `.gitlab-ci.yml` file.  To do this, you will need to install the `gitlab-runner` for your OS and, preferably, Docker-CE.  You can then use the Docker executor to run the jobs.

Any environment variables that would normally be set by GitLab's CI/CD process must be passed into the build environment.  Please read the job in question to verify you have all possible keys/secrets already configured and take special care to **NOT COMMIT SECRETS** to the repository.  For convenience, the file name `local-runner-env` has been added to the `.gitignore`.  Feel free to use that file name for a script like this, which stores the variables as strings in an array and then prints each as a `--env VAR=val` argument:

```
# local-runner-env
ENV_VARS=(
SPECIAL_USER=somebody
SPECIAL_PASSWORD=password
)
printf " --env %s" "${ENV_VARS[@]}"
```

And then if we had a `printenv` job, we could execute it like this:

```
[~/project]$ gitlab-runner exec docker $(. ./local-runner-env) printenv

Running with gitlab-runner 11.0.0 (5396d320)
Using Docker executor with image alpine:latest ...
Pulling docker image alpine:latest ...
Using docker image sha256:3fd9065eaf02feaf94d68376da52541925650b81698c53c6824d92ff63f98353 for alpine:latest ...
Running on runner--project-0-concurrent-0 via some.host.com...
Cloning repository...
Cloning into '/builds/project-0'...
done.
Checking out 355f773c as master...
Skipping Git submodules setup
$ printenv
CI_SERVER_REVISION=
CI=true
CI_RUNNER_REVISION=5396d320
HOSTNAME=runner--project-0-concurrent-0
CI_JOB_STAGE=build
CI_SERVER_VERSION=
SHLVL=2
OLDPWD=/
SPECIAL_USER=somebody
SPECIAL_PASSWORD=password
HOME=/root
CI_JOB_ID=1
CI_COMMIT_REF_NAME=master
CI_RUNNER_VERSION=11.0.0
CI_PROJECT_ID=0
GITLAB_CI=true
CI_COMMIT_SHA=355f773c471add104ab17f984ce5016001813b62
CI_PROJECT_DIR=/builds/project-0
CI_SERVER_NAME=GitLab CI
CI_JOB_TOKEN=
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
CI_SERVER=yes
CI_REPOSITORY_URL=/home/user/project
CI_RUNNER_EXECUTABLE_ARCH=linux/amd64
CI_DISPOSABLE_ENVIRONMENT=true
PWD=/builds/project-0
```

 > **Important 1:** THe CI feature that obfuscates secrets within the build logs _does not exist_ when running locally.  Any exposure of those variables to the logging environment when running locally will appear in plain text!

 > **Important 2:** The above method will not work for multi-line variables like SSH keys.

 > Note: Running a job locally has the drawback that your changes must be committed (pushing is not required).  You may find it helpful to `git commit --amend` as you work through changes and then `git reset HEAD^` to begin splitting the commit into real changes that you plan to push (`git add --patch`, for example).
