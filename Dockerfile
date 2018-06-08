# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of Geon's REST-Python.
#
# REST-Python is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REST-Python is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#

FROM geontech/redhawk-runtime:2.0.8
LABEL name="REST-Python Web Server" \
    description="Geon's Fork of REST-Python" \
    maintainer="Thomas Goodwin <btgoodwin@geontech.com>"

# Build-time configurable variables
ARG REST_PYTHON_PORT=8080

# Runtime variables
ENV REST_PYTHON_PORT=${REST_PYTHON_PORT}

# Expose the configured default port.
EXPOSE ${REST_PYTHON_PORT}

RUN yum install -y \
    git \
    gcc \
    python-dev \
    curl \
    python-virtualenv && \
    yum clean all -y

# Install and update pip
RUN curl https://bootstrap.pypa.io/get-pip.py | python && \
    pip install -U pip

# Install the rest-python server requirements
COPY ./setup.sh ./pyvenv ./requirements.txt /opt/rest-python/
WORKDIR /opt/rest-python
RUN ./setup.sh install && pip install -r requirements.txt

# Install the rest of the rest-python server and launcher
COPY . /opt/rest-python
RUN cp docker/rest-python.conf /etc/supervisor.d/rest-python.conf && \
    cp docker/kill_supervisor.py /usr/bin/kill_supervisor.py && \
    chmod u+x /usr/bin/kill_supervisor.py

# Mount point for end-user apps
VOLUME /opt/rest-python/apps

CMD ["/usr/bin/supervisord"]
