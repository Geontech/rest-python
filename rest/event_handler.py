#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK server.
#
# REDHAWK server is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK server is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
import logging
from tornado import ioloop, websocket
from rest.crossdomainsocket import CrossDomainSockets
from handler import JsonHandler
from helper import PropertyHelper
import json
from tornado import gen

class EventHandler(CrossDomainSockets):

    def initialize(self, redhawk, _ioloop=None):
        self.redhawk = redhawk
        self.handlerType = None

        # explicit ioloop for unit testing
        if not _ioloop:
            _ioloop = ioloop.IOLoop.instance()

        self.ioloop = _ioloop

    def open(self, arg):
        # register event handling.  Arg will be either `redhawk` or `events`
        # representing the outermost REDHAWK subsystem watcher, or the
        # event channels, filtered down to a specific domain.
        if 'redhawk' == arg:
            self.handlerType = arg
            self.redhawk.add_redhawk_listener(self._post_event)
            logging.debug('REDHAWK Event Handler OPEN')
        elif 'events' == arg:
            self.handlerType = arg
            logging.debug('EVENT CHANNEL Event Handler OPEN')
        else:
            logging.error('Unknown Event Handler: {0}'.format(arg))

    def on_message(self, message):
        logging.debug('stream message[%d]: %s', len(message), message)
        message = json.loads(message)
        if 'events' == self.handlerType:
            # Message format is {command: ADD/REMOVE, topic:channel_name, domainId:domainId }
            command = message.get('command', None)
            domainId = message.get('domainId', None)
            topic = message.get('topic', None)
            if domainId and topic:
                if   'ADD'    == command:
                    self.redhawk.add_event_listener(self._post_event, domainId, topic)
                    logging.debug('EVENT CHANNEL Event Handler subscribing to {0}:{1}'.format(domainId, topic))
                elif 'REMOVE' == command:
                    self.redhawk.rm_event_listener(self._post_event, domainId, topic)
                    logging.debug('EVENT CHANNEL Event Handler unsubscribing to {0}:{1}'.format(domainId, topic))
                else:
                    logging.error('Unknown command received: {0}'.format(command))
            else:
                logging.error('Invalid message format sent to EventHandler: {0}'.format(message))

    def on_close(self):
        if 'status' == self.handlerType:
            logging.debug('REDHAWK Event Handler CLOSE')
            self.redhawk.rm_redhawk_listener(self._post_event)
        elif 'msg' == self.handlerType:
            logging.debug('EVENT CHANNEL Event Handler CLOSE')
            self.redhawk.rm_event_listener(self._post_event)

    def _post_event(self, event):
        # if connection still open, post the next event
        self.ioloop.add_callback(self.write_message, event)

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(EventHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')


class EventChannelHandler(JsonHandler, PropertyHelper):
    @gen.coroutine
    def get(self, number=150, *args):
        try:
            number = int(float(number))
        except:
            number = 150
        eventChannels = yield self.redhawk.get_all_event_channels(number)
        eventChannels = list(set(eventChannels))
        channels = {'eventChannels':eventChannels}
        self._render_json(channels)


        

