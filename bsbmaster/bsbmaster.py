#!/usr/bin/env python

# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:si:et:enc=utf-8

# Author: Ivan A-R <ivan@tuxotronic.org>
# Project page: http://tuxotronic.org/wiki/projects/stm32loader
#
# This file is part of stm32loader.
#
# stm32loader is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3, or (at your option) any later
# version.
#
# stm32loader is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with stm32loader; see the file COPYING3.  If not see
# <http://www.gnu.org/licenses/>.

import sys, getopt
import serial
import time
import gatewaycom

import construct
import protocol


try:
    from progressbar import *
    usepbar = 1
except:
    usepbar = 0

# Verbose level
QUIET = 20

def mdebug(level, message):
    if(QUIET >= level):
        print >> sys.stderr , message


class CmdException(Exception):
    pass

class FlashConnection:
    def __init__(self, conManager, node_id, send_queue, flash_state='INIT'):
        self.conManager = conManager
        self.sender_id = sender_id
        self.flash_state = flash_state
        self.send_queue = send_queue
        self.base_container = construct.Container{
            frametype = 'CAN_MSG',
            priority = 'REGULAR',
            subnet = 'ZERO',
            protocol = 'FLASH',
            receiver = node_id,
            sender = 'ADDR_GW'
        )
        self.total_bytes = None
        self.total_batches = None
        
    def processFrame(self,container)
        data = container.can_msg_data
        if data.data_counter == 'COMMAND':
            command = data.command
            if command == 'RESET_ACK':
                self.flash_state = 'NODE_RESET'
            elif command == 'BOOTLOADER_READY':
                self.flash_state = 'NODE_READY'
                self.sendFlashRequest()
            elif command == 'BOOTLOADER_ERROR':
                return 'ERROR'
            elif command == 'FLASH_ACK' and self.flash_state =='NODE_READY':
                self.flash_state = 'FLASH_HANDSHAKE'
                self.sendFlashDetails()
            elif command == 'FLASH_DETAILS_ACK' and self.flash_state =='FLASH_HANDSHAKE':
                self.flash_state = 'FLASH_READY'
                self.initTransfer('FIRST')
            elif command == 'BATCH_READY_ACK' and
                    ( self.flash_state =='FLASH_READY' or self.flash_state =='BATCH_COMPLETE' or
                      self.flash_state =='BATCH_RETRANSMIT' ):
                self.flash_state = 'SEND_BATCH'
                self.sendNextBatch()
            elif command == 'BATCH_COMPLETE_ACK' and self.flash_state =='SEND_BATCH':
                self.flash_state = 'BATCH_COMPLETE'
                self.initTransfer('NEXT') #also send CRC at end!
            elif command == 'BATCH_RETRANSMIT_REQ' and self.flash_state =='BATCH_COMPLETE':
                self.flash_state = 'BATCH_RETRANSMIT'
                self.initTransfer('LAST') #also send CRC at end!
            elif command == 'CRC_ACK' and self.flash_state =='BATCH_COMPLETE':
                self.flash_state = 'CRC_OK'
                return 'DONE'
            elif command == 'APP_START_ACK':
                return 'DONE'
            else:
                return 'UNKNOWN'
        return 'OK'
            
    def sendFlashRequest(self):
        cont = self.base_container
        data_cont = construct.Container(
            data_counter = 'COMMAND',
            command = 'FLASH_REQ'
        )
        cont.update( construct.Container( can_msg_data = data_cont ))
        self.send_queue.put(cont)
        
    def sendFlashDetails(self):
        cont = self.base_container
        data_cont = construct.Container(
            data_counter = 'COMMAND',
            command = 'FLASH_DETAILS',
            total_bytes = self.total_bytes,
            total_batches = self.total_batches
        )
        cont.update( construct.Container( can_msg_data = data_cont ))
        self.send_queue.put(cont)
        
    def initTransfer(self, order):
    
    def sendNextBatch(self):
                
            
class ComManager(threading.Thread):
    def __init__(self, host, port):
        super(ComManager, self).__init__()
        self.logger = logging.getLogger('bsbmaster')
        self.daemon = True
        self.stopped = False
        self.receive_queue = Queue.Queue()
        self.send_queue = Queue.Queue()
        self.flash_connections = {}
        self._connManager = gatewaycom.ConnectionManager(host, port, receive_queue, send_queue)
        self._connManager.start()
            
    def run(self):
        self.logger.info('ComManager started')
        while not self.stopped:
            while self.receive_queue:
                con_status = None
                flash_connection = None
                container = receive_queue.get()
                if container.sender in self.flash_connections:
                    flash_connection = flash_connections[container.sender]                    
                else:
                    flash_connection = FlashConnection(container.sender)
                    flash_connections[container.sender] = flash_connection
                con_status = flash_connection.processFrame(container)
                if con_status in ['DONE','UNKNOWN','ERROR']:
                    del self.flash_connections[flash_connection]
        self.logger.info('Closing ComManager...')
        try:
            self.stop()
        except Exception, e:
            pass
        self.logger.info('ComManager stopped')
        
    def stop(self):
        try:
            self._connManager.stop()
        except: Exception, e:
           self.logger.info("Exception when stopping ConnectionManager!")
            self.logger.info(e)
        self.stopped = True
    
    def deleteConnection(self,con_name):
        
    
    def triggerNode(self, node_id):
        trigger_container = construct.Container{
            frametype = 'CAN_MSG',
            priority = 'REGULAR',
            subnet = 'ZERO',
            protocol = 'FLASH',
            receiver = node_id,
            sender = 'ADDR_GW',
            can_msg_data = construct.Container(
                data_counter = 'COMMAND',
                command = 'RESET_REQ'
            )
        )
        self.send_queue.put(trigger_container)
        
    def startNodeApp(self, node_id):
        start_container = construct.Container{
            frametype = 'CAN_MSG',
            priority = 'REGULAR',
            subnet = 'ZERO',
            protocol = 'FLASH',
            receiver = node_id,
            sender = 'ADDR_GW',
            can_msg_data = construct.Container(
                data_counter = 'COMMAND',
                command = 'APP_START_REQ'
            )
        )
        self.send_queue.put(start_container)
                            
class CommandInterface:
    def _encode_addr(self, addr):
        byte3 = (addr >> 0) & 0xFF
        byte2 = (addr >> 8) & 0xFF
        byte1 = (addr >> 16) & 0xFF
        byte0 = (addr >> 24) & 0xFF
        crc = byte0 ^ byte1 ^ byte2 ^ byte3
        return (chr(byte0) + chr(byte1) + chr(byte2) + chr(byte3) + chr(crc))


    def cmdReadMemory(self, addr, lng):
        assert(lng <= 256)
        if self.cmdGeneric(0x11):
            mdebug(10, "*** ReadMemory command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x11 address failed")
            N = (lng - 1) & 0xFF
            crc = N ^ 0xFF
            self.sp.write(chr(N) + chr(crc))
            self._wait_for_ask("0x11 length failed")
            return map(lambda c: ord(c), self.sp.read(lng))
        else:
            raise CmdException("ReadMemory (0x11) failed")


    def cmdGo(self, addr):
        if self.cmdGeneric(0x21):
            mdebug(10, "*** Go command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x21 go failed")
        else:
            raise CmdException("Go (0x21) failed")


    def cmdWriteMemory(self, addr, data):
        assert(len(data) <= 256)
        if self.cmdGeneric(0x31):
            mdebug(10, "*** Write memory command")
            self.sp.write(self._encode_addr(addr))
            self._wait_for_ask("0x31 address failed")
            #map(lambda c: hex(ord(c)), data)
            lng = (len(data)-1) & 0xFF
            mdebug(10, "    %s bytes to write" % [lng+1]);
            self.sp.write(chr(lng)) # len really
            crc = 0xFF
            for c in data:
                crc = crc ^ c
                self.sp.write(chr(c))
            self.sp.write(chr(crc))
            self._wait_for_ask("0x31 programming failed")
            mdebug(10, "    Write memory done")
        else:
            raise CmdException("Write memory (0x31) failed")


    def cmdEraseMemory(self, sectors = None):
        if self.cmdGeneric(0x43):
            mdebug(10, "*** Erase memory command")
            if sectors is None:
                # Global erase
                self.sp.write(chr(0xFF))
                self.sp.write(chr(0x00))
            else:
                # Sectors erase
                self.sp.write(chr((len(sectors)-1) & 0xFF))
                crc = 0xFF
                for c in sectors:
                    crc = crc ^ c
                    self.sp.write(chr(c))
                self.sp.write(chr(crc))
            self._wait_for_ask("0x43 erasing failed")
            mdebug(10, "    Erase memory done")
        else:
            raise CmdException("Erase memory (0x43) failed")

# Complex commands section

    def readMemory(self, addr, lng):
        data = []
        if usepbar:
            widgets = ['Reading: ', Percentage(),', ', ETA(), ' ', Bar()]
            pbar = ProgressBar(widgets=widgets,maxval=lng, term_width=79).start()
        
        while lng > 256:
            if usepbar:
                pbar.update(pbar.maxval-lng)
            else:
                mdebug(5, "Read %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': 256})
            data = data + self.cmdReadMemory(addr, 256)
            addr = addr + 256
            lng = lng - 256
        if usepbar:
            pbar.update(pbar.maxval-lng)
            pbar.finish()
        else:
            mdebug(5, "Read %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': 256})
        data = data + self.cmdReadMemory(addr, lng)
        return data

    def writeMemory(self, addr, data):
        lng = len(data)
        if usepbar:
            widgets = ['Writing: ', Percentage(),' ', ETA(), ' ', Bar()]
            pbar = ProgressBar(widgets=widgets, maxval=lng, term_width=79).start()
        
        offs = 0
        while lng > 256:
            if usepbar:
                pbar.update(pbar.maxval-lng)
            else:
                mdebug(5, "Write %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': 256})
            self.cmdWriteMemory(addr, data[offs:offs+256])
            offs = offs + 256
            addr = addr + 256
            lng = lng - 256
        if usepbar:
            pbar.update(pbar.maxval-lng)
            pbar.finish()
        else:
            mdebug(5, "Write %(len)d bytes at 0x%(addr)X" % {'addr': addr, 'len': 256})
        self.cmdWriteMemory(addr, data[offs:offs+lng] + ([0xFF] * (256-lng)) )




	def __init__(self) :
        pass


def usage():
    print """Usage: %s [-hqVewvr] [-l length] [-p port] [-b baud] [-a addr] [file.bin]
    -h          This help
    -q          Quiet
    -V          Verbose
    -e          Erase
    -w          Write
    -v          Verify
    -r          Read
    -l length   Length of read
    -p port     TCP port (default: 23)
    -a addr     Target bus address
    -i ip       Gateway IP address (default: 10.43.100.112)

    ./bsbmaster.py -e -w -v example/main.bin

    """ % sys.argv[0]
    

if __name__ == "__main__":
    conf = {
            'port': 23,
            'ip': '10.43.100.112',
            'address': 0x08000000,
            'erase': 0,
            'write': 0,
            'verify': 0,
            'read': 0,
            'len': 1000,
            'fname':'main.bin',
        }

# http://www.python.org/doc/2.5.2/lib/module-getopt.html

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hqVewvrp:i:a:l:")
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    QUIET = 5

    for o, a in opts:
        if o == '-V':
            QUIET = 10
        elif o == '-q':
            QUIET = 0
        elif o == '-h':
            usage()
            sys.exit(0)
        elif o == '-e':
            conf['erase'] = 1
        elif o == '-w':
            conf['write'] = 1
        elif o == '-v':
            conf['verify'] = 1
        elif o == '-r':
            conf['read'] = 1
        elif o == '-p':
            conf['port'] = a
        elif o == '-i':
            conf['ip'] = eval(a)
        elif o == '-a':
            conf['address'] = eval(a)
        elif o == '-l':
            conf['len'] = eval(a)
        else:
            assert False, "unhandled option"

    cmd = CommandInterface()
    cmd.open(conf['port'], conf['ip'])
    mdebug(10, "Open connection %(ip)s:%(port)d" % {'ip':conf.['ip'],'port':conf['port']})
    try:
        try:
            cmd.initChip()
        except:
            print "Can't init. Ensure that BOOT0 is enabled and reset device"

        bootversion = cmd.cmdGet()
        mdebug(0, "Bootloader version %X" % bootversion)
        mdebug(0, "Chip id `%s'" % str(map(lambda c: hex(ord(c)), cmd.cmdGetID())))
#    cmd.cmdGetVersion()
#    cmd.cmdGetID()
#    cmd.cmdReadoutUnprotect()
#    cmd.cmdWriteUnprotect()
#    cmd.cmdWriteProtect([0, 1])

        if (conf['write'] or conf['verify']):
            #data = map(lambda c: ord(c), file(args[0]).read())
            # line altered following comment in blog post 1 feb 2011
            data = map(lambda c: ord(c), file(args[0], 'rb').read()) 
        if conf['erase']:
            cmd.cmdEraseMemory()

        if conf['write']:
            cmd.writeMemory(conf['address'], data)

        if conf['verify']:
            verify = cmd.readMemory(conf['address'], len(data))
            if(data == verify):
                print "Verification OK"
            else:
                print "Verification FAILED"
                print str(len(data)) + ' vs ' + str(len(verify))
                for i in xrange(0, len(data)):
                    if data[i] != verify[i]:
                        print hex(i) + ': ' + hex(data[i]) + ' vs ' + hex(verify[i])

        if not conf['write'] and conf['read']:
            rdata = cmd.readMemory(conf['address'], conf['len'])
#            file(conf['fname'], 'wb').write(rdata)
            file(args[0], 'wb').write(''.join(map(chr,rdata)))

#    cmd.cmdGo(addr + 0x04)
    finally:
        cmd.releaseChip()
