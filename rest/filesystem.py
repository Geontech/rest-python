#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK rest-python.
#
# REDHAWK rest-python is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK rest-python is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
"""
Rest handlers for filesystems

Classes:
FileSystems -- Get info
"""

from tornado import gen

from handler import JsonHandler

import json

class FileSystem(JsonHandler):
    @gen.coroutine
    def get(self, domain_name, path):
        try:
            info = yield self.redhawk.get_path(domain_name, str(path))

            self._render_json(info)
        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def post(self, domain_name, path):
        try:
            if self.request.body:
                data = json.loads(self.request.body)

                # Use the path in the URI as the destination and expect a path in the body as the source
                method = data.get('method')
                if method in ['copy', 'move']:
                    fromPath = str(data['from_path'])

                    info = yield self.redhawk.move(domain_name, fromPath, str(path), data['method'] == 'copy')
                # Create a directory or a file based on the path ending with a / or not. If a / is present
                # but contents are also present, a file will be created instead of a directory
                elif method == 'create':
                    contents = str(data.get('contents', ''))
                    readOnly = data.get('read_only', False)

                    info = yield self.redhawk.create(domain_name, str(path), contents, readOnly)
                else:
                    raise Exception('Unknown file system POST method: %s' % method)
            else:
                # Create a directory or a file based on the path ending with a / or not.
                info = yield self.redhawk.create(domain_name, str(path), None, False)
     
            self._render_json(info)
        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def put(self, domain_name, path):
        try:
            if self.request.body:
                data = json.loads(self.request.body)
                method = data.get('method')
                if method == 'append':
                    contents = str(data.get('contents'))

                    info = yield self.redhawk.append(domain_name, str(path), contents)
                elif method == 'replace':
                    contents = str(data.get('contents'))

                    info = yield self.redhawk.replace(domain_name, str(path), contents)
                else:
                    raise Exception('Unknown file system PUT method: %s' % method)

                self._render_json(info)
            else:
                raise Exception('File system PUT requires a body')

        except Exception as e:
            self._handle_request_exception(e)

    @gen.coroutine
    def delete(self, domain_name, path):
        try:
            info = yield self.redhawk.remove(domain_name, str(path))

            self._render_json(info)
        except Exception as e:
            self._handle_request_exception(e)
