import socket, time, random, struct, threading, signal
import logging, copy

import protocol
import construct

class ConnectionManager(threading.Thread):
    def __init__(self,  host, port, receive_queue, send_queue):
        super(ConnectionManager, self).__init__()
        self.logger = logging.getLogger('sender')
        self.host = host
        self.port = port
        self.receive_queue = receive_queue
        self.send_queue = send_queue
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
