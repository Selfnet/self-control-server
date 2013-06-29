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
    def __init__(self, conManager, sender_id, flash_state='INIT'):
        self.conManager = conManager
        self.sender_id = sender_id
        self.flash_state = flash_state
        
    def processFrame(self,container)
        data = container.can_msg_data
        if data.data_counter == 'COMMAND':
            command = data.command
            if command == 'RESET_ACK':
                self.flash_state = 'NODE_RESET'
            elif command == 'BOOTLOADER_READY':
                self.flash_state = 'NODE_READY'
            elif command == 'BOOTLOADER_ERROR':
                return 'ERROR'
            elif command == 'FLASH_ACK' and self.flash_state =='NODE_READY':
                self.flash_state = 'FLASH_HANDSHAKE'
                self.sendFlashDetails()
            elif command == 'FLASH_DETAILS_ACK' and self.flash_state =='FLASH_HANDSHAKE':
                self.flash_state = 'FLASH_READY'
                self.initTransfer()
            elif command == 'BATCH_READY_ACK' and
                    ( self.flash_state =='FLASH_READY' or self.flash_state =='BATCH_COMPLETE' or
                      self.flash_state =='BATCH_RETRANSMIT' ):
                self.flash_state = 'SEND_BATCH'
                self.sendNextBatch()
            elif command == 'BATCH_COMPLETE_ACK' and self.flash_state =='SEND_BATCH':
                self.flash_state = 'BATCH_COMPLETE'
                self.continueTransfer() #also send CRC at end!
            elif command == 'BATCH_RETRANSMIT_REQ' and self.flash_state =='BATCH_COMPLETE':
                self.flash_state = 'BATCH_RETRANSMIT'
                self.reTransfer() #also send CRC at end!
            elif command == 'CRC_ACK' and self.flash_state =='BATCH_COMPLETE':
                self.flash_state = 'CRC_OK'
                self.sendResetReq()
            elif command == 'APP_START_ACK' and self.flash_state =='CRC_OK':
                return 'DONE'
            else:
                return 'UNKNOWN'
        return 'OK'
            
    def 
                
            
class ComManager(threading.Thread):
    def __init__(self, receive_queue, send_queue):
        super(ComManager, self).__init__()
        self.logger = logging.getLogger('bsbmaster')
        self.daemon = True
        self.stopped = False
        self.receive_queue = receive_queue
        self.send_queue = send_queue
        self.flash_connections = {}
            
    def run(self):
        self.logger.info('ComManager started')
        while not self.stopped:
            while self.receive_queue:
                container = receive_queue.get()
                if container.sender in self.flash_connections:
                    flash_connection = flash_connections[container.sender]
                    flash_connection.processFrame(container)
                else:
                    flash_connection = FlashConnection(container.sender)
                    flash_connections[container.sender] = flash_connection
                    flash_connection.processFrame(container)
        self.logger.info('Closing ComManager...')
        try:
            self.stop()
        except Exception, e:
            pass
        self.logger.info('ComManager stopped')
        
    def stop(self):
        self.stopped = True
        self.disconnect()
    
    def deleteConnection(self,con_name):
        del self.flash_connections[con_name]
    
    def triggerNode(self, node_id):
        trigger_container = construct.Container{
            frametype = 'CAN_MSG',
            priority = 'REGULAR',
            subnet = 'ZERO',
            protocol = 'FLASH',
            receiver = node_id,
            sender = 'ADDR_GW',
            construct.Container(
                data_counter = 'COMMAND',
                command = 'RESET_REQ'
            )
        )
        self.send_queue.put(trigger_container)
                            
class CommandInterface:
    def open(self,host,port):
        self._connManager = ConnectionManager(host, port)
        self._connManager.start()

    def initChip(self):

        return self._wait_for_ask("Syncro")

    def releaseChip(self):
        self.sp.setRTS(1)
        self.reset()

    def cmdGeneric(self, cmd):
        self.sp.write(chr(cmd))
        self.sp.write(chr(cmd ^ 0xFF)) # Control byte
        return self._wait_for_ask(hex(cmd))

    def cmdGet(self):
        if self.cmdGeneric(0x00):
            mdebug(10, "*** Get command");
            len = ord(self.sp.read())
            version = ord(self.sp.read())
            mdebug(10, "    Bootloader version: "+hex(version))
            dat = map(lambda c: hex(ord(c)), self.sp.read(len))
            mdebug(10, "    Available commands: "+str(dat))
            self._wait_for_ask("0x00 end")
            return version
        else:
            raise CmdException("Get (0x00) failed")

    def cmdGetVersion(self):
        if self.cmdGeneric(0x01):
            mdebug(10, "*** GetVersion command")
            version = ord(self.sp.read())
            self.sp.read(2)
            self._wait_for_ask("0x01 end")
            mdebug(10, "    Bootloader version: "+hex(version))
            return version
        else:
            raise CmdException("GetVersion (0x01) failed")

    def cmdGetID(self):
        if self.cmdGeneric(0x02):
            mdebug(10, "*** GetID command")
            len = ord(self.sp.read())
            id = self.sp.read(len+1)
            self._wait_for_ask("0x02 end")
            return id
        else:
            raise CmdException("GetID (0x02) failed")


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

    def cmdWriteProtect(self, sectors):
        if self.cmdGeneric(0x63):
            mdebug(10, "*** Write protect command")
            self.sp.write(chr((len(sectors)-1) & 0xFF))
            crc = 0xFF
            for c in sectors:
                crc = crc ^ c
                self.sp.write(chr(c))
            self.sp.write(chr(crc))
            self._wait_for_ask("0x63 write protect failed")
            mdebug(10, "    Write protect done")
        else:
            raise CmdException("Write Protect memory (0x63) failed")

    def cmdWriteUnprotect(self):
        if self.cmdGeneric(0x73):
            mdebug(10, "*** Write Unprotect command")
            self._wait_for_ask("0x73 write unprotect failed")
            self._wait_for_ask("0x73 write unprotect 2 failed")
            mdebug(10, "    Write Unprotect done")
        else:
            raise CmdException("Write Unprotect (0x73) failed")

    def cmdReadoutProtect(self):
        if self.cmdGeneric(0x82):
            mdebug(10, "*** Readout protect command")
            self._wait_for_ask("0x82 readout protect failed")
            self._wait_for_ask("0x82 readout protect 2 failed")
            mdebug(10, "    Read protect done")
        else:
            raise CmdException("Readout protect (0x82) failed")

    def cmdReadoutUnprotect(self):
        if self.cmdGeneric(0x92):
            mdebug(10, "*** Readout Unprotect command")
            self._wait_for_ask("0x92 readout unprotect failed")
            self._wait_for_ask("0x92 readout unprotect 2 failed")
            mdebug(10, "    Read Unprotect done")
        else:
            raise CmdException("Readout unprotect (0x92) failed")


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



class ConnectionManager(threading.Thread):
    def __init__(self,  host, port):
        super(ConnectionManager, self).__init__()
        self.logger = logging.getLogger('sender')
        self.host = host
        self.port = port
        self.receive_queue = Queue.queue
        self.send_queue = Queue.queue
        self.connected = False
        self.stopped = False
        self.lastReceivedPlain = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.pongCallbacks = []
        self.pingContainer = construct.Container(
                    frametype = 'CAN_MSG',
                    priority = 'REGULAR',
                    subnet = 'ZERO',
                    protocol = 'PING',
                    receiver = 'ADDR_BC',
                    sender = 'ADDR_GW',
                    length = 1,
                    data = [0xFF]
        )
    
    def run(self):
        print 'ConnectionManager started. Trying to connect...'
        self.logger.info('ConnectionManager started. Trying to connect...')
        while not self.stopped:
            if not self.connected:
                self.tryconnect()
            else:
                try:
                    received = None
                    received = self.sock.recv(4096)
                    if not self.stopped:
                        if received:
                            self.logger.debug("received unicode: %s"%str(received))
                            self.logger.debug("received hex: %s"%Helper.hexdump(received))
                            for container in protocol.PacketHandler().parse(received):
                                self.logger.debug('Received container %s'%str(container))
                                try:
                                    if container['frametype'] == 'CAN_MSG':
                                        if container['protocol'] == 'FLASH':
                                            self.receive_queue.put(container)
                                    else:
                                        pass
                                except Exception, e:
                                    self.logger.debug('exception when interpreting container: %s'%str(e))
                                    self.logger.exception(e)
                        else:
                            self.connectionReset()
                        if self.send_queue:
                            while self.send_queue:
                                container = self.send_queue.get()
                                self.sendContainer(container)                                
                except socket.timeout, e:
                    pass
                except Exception, e:
                    self.logger.debug('in statechecker exception: %s'%str(e))
                    self.logger.exception(e)
                    self.connectionReset()
                    
        self.logger.info('Closing connection...')
        try:
            self.stop()
        except Exception, e:
            pass
        self.logger.info('Connection closed, ConnectionManager stopped')
    
    def connectionReset(self):
        self.logger.debug("connection reset")
        print "Connection lost. Reconnecting..."
        self.connected = False
        self.lastReceived = 'Connection error'
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1)
        self.sock.connect((self.host, self.port))
        self.connected = True
        self.logger.debug("connection established")
        print "Connected to %s:%d"%(self.host,self.port)
    
    def stop(self):
        self.stopped = True
        self.disconnect()
    
    def disconnect(self):
        self.sock.close()
        self.logger.debug("disconnect")
        self.connected = False
    
    def tryconnect(self):
        try:
            self.disconnect()
        except:
            pass
        self.logger.debug("Trying to connect...")
        while not self.connected and not self.stopped:
            try:
                self.connect()
                self.logger.info("Connected to %s:%d"%(self.host,self.port))
            except socket.timeout:
                pass
            except Exception, e:
                self.logger.info(e)
                time.sleep(0.1)
                self.logger.debug("Trying to connect...")
                
    def sendContainer(self,container,log=True):
        ret = 0
        payload = ''
        
        try:
            payload = protocol.gw_msg.build(container)
        except Exception,e:
            self.logger.error('Cannot build container: %s'%str(container))
            self.logger.error('Exception when building container: %s'%str(e))
            self.logger.exception(e)
            ret = 1

        #hexdump = Helper.hexdump(payload)
        #bindump = Helper.bindump(payload)
        if log:
            logging.getLogger('sender').debug('Sending container\n%s\n' % str(container))
            print "test"
        self.send(payload, log)

    def send(self, msg, log=True):
        if self.connected:
            if log:
                self.logger.debug("waiting for sendLock...")
            if log:
                self.logger.debug("sendLock acquired")
                self.logger.info("sending unicode \t%s"%msg)
            hexmsg = ''
            binmsg = ''
            for c in msg:
                binmsg += Helper.format8bit(bin(struct.unpack('B',c)[0])) + ' '
                hexmsg += hex(struct.unpack('B',c)[0]) + ' '
            if log:
                self.logger.info("sending binary %s"%binmsg)
                self.logger.info("sending hex %s"%Helper.hexdump(msg))
            try:
                self.sock.sendall(msg)
            except Exception, e:
                self.logger.warn('Exception when sending: %s'%str(e))
                print "Connection error. Reconnecting..."
                self.connectionReset()
        else:
            self.logger.warn("Not sent. Socket not connected")




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
