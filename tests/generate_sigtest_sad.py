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
from ossie.utils import redhawk

from defaults import Default

def main():
    FILE_NAME = '{0}.sad.xml'.format(Default.WAVEFORM)
    INSTALL_DIR = os.path.join('/', 'waveforms', Default.WAVEFORM)
    INSTALL_FILE = os.path.join(INSTALL_DIR, FILE_NAME)

    # Make a simple waveform and write it to file
    sb.launch(Default.COMPONENT)
    waveform_xml = sb.generateSADXML(Default.WAVEFORM)

    # Install the waveform in the SDRROOT of the running domain
    domain_name = os.getenv('DOMAINNAME', 'REDHAWK_DEV')
    omniorb_ip = os.getenv('OMNISERVICEIP', 'localhost')
    try:
        print 'Attaching to domain "{0}" on naming service "{1}"'.format(
            domain_name, omniorb_ip)
        dom = redhawk.attach(domain_name, omniorb_ip)

        if not dom.fileMgr.exists(INSTALL_DIR):
            print 'Creating ' + INSTALL_DIR
            dom.fileMgr.mkdir(INSTALL_DIR)
        print 'Writing ' + INSTALL_FILE
        waveform_sca = dom.fileMgr.create(INSTALL_FILE)
        waveform_sca.write(waveform_xml)
        print 'Finished.  Closing file.'
        waveform_sca.close()
    except:
        pass

if __name__ == '__main__':
    print main()
