#!/usr/bin/env python
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

import os
from ossie.utils import sb

from defaults import Default

def main():
    SDRROOT = os.environ['SDRROOT']
    FILE_NAME = '{0}.sad.xml'.format(Default.WAVEFORM)
    INSTALL_DIR = os.path.join(SDRROOT, 'dom', 'waveforms', Default.WAVEFORM)
    INSTALL_FILE = os.path.join(INSTALL_DIR, FILE_NAME)

    # Make a simple waveform and write it to file
    siggen = sb.launch(Default.COMPONENT)
    waveform = sb.generateSADXML(Default.WAVEFORM)

    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
    
    with open(INSTALL_FILE, 'w+') as sad:
        sad.write(waveform)

    return INSTALL_FILE

if __name__ == '__main__':
    print main()