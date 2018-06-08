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
import time
from ossie.utils import sb
from ossie.utils import redhawk
from ossie.cf import CF

from defaults import Default

def fei_filename_format(file_handle, CF, SR, BW=None, TYPE='B', R=False):
    '''
    The format is fileHandle_CF_SR<_BW>.TYPE<R> where:
    - file_handle: Any handle used to identify data (with no _'s present)
    - CF: The center frequency of the data
    - SR: The sample rate of the data
    - BW: The optional bandwidth. If not included, use optional complex specifier to determine bandwidth
    - TYPE: The type of data (B, I, UB, etc.) based on MIDAS format
    - R: When present, the data is treated as real, otherwise, complex
    '''
    fn = '_'.join([str(n) for n in [file_handle, CF, SR]])

    if BW:
        fn = '_'.join([str(n) for n in [fn, BW]])
    '.'.join([fn, TYPE])

    if R:
        fn += 'R'
    return fn


def main():
    FILE_NAME = fei_filename_format(
        file_handle='testTone',
        CF=Default.FEI_ALLOC_CF,
        SR=Default.FEI_ALLOC_SR,
        BW=Default.FEI_ALLOC_BW,
        TYPE=Default.FEI_ALLOC_TYPE,
        R=Default.FEI_ALLOC_R)
    SNAPSHOT_DIR = '/tmp'
    SNAPSHOT_FILE = os.path.join(SNAPSHOT_DIR, FILE_NAME) 

    # Setup a siggen and filewriter 
    siggen = sb.launch('rh.SigGen')
    siggen.configure({ 'sample_rate': Default.FEI_ALLOC_SR })

    # Launch a FileWriter, configured for BLUE format
    filewriter = sb.launch('rh.FileWriter')
    filewriter.configure({ 'destination_uri': 'file://{0}'.format(SNAPSHOT_FILE)})

    # Connect short interfaces together
    port = siggen.getPort('dataShort_out')._narrow(CF.Port)
    port.connectPort(filewriter.getPort('dataShort_in'), 'snapshot')

    # Start, wait, stop, release... File should be saved off at that point.
    sb.start()
    time.sleep(2)
    sb.stop()

    # Attach to the domain and copy the file over.
    domain_name = os.getenv('DOMAINNAME', 'REDHAWK_DEV')
    omniorb_ip = os.getenv('OMNISERVICEIP', 'localhost')
    try:
        print 'Attaching to domain "{0}" on naming service "{1}"'.format(domain_name, omniorb_ip)
        dom = redhawk.attach(domain_name, omniorb_ip)

        sca_filename = os.path.join(Default.FEI_FILE_PATH, FILE_NAME)
        print 'Creating ' + sca_filename
        if not dom.fileMgr.exists(Default.FEI_FILE_PATH):
            dom.fileMgr.mkdir(Default.FEI_FILE_PATH)
        snap_sca = dom.fileMgr.create(sca_filename)

        print 'Copying ' + SNAPSHOT_FILE + ' to SCA file system'
        with open(SNAPSHOT_FILE) as snap_local:
            snap_sca.write(snap_local.read())

        print 'Finished.  Closing file.'
        snap_sca.close()
    except:
        print 'Exception!'
        pass

    print 'Removing original file.'
    os.remove(SNAPSHOT_FILE)

if __name__ == '__main__':
    print main()

