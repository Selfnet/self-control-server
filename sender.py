import socket, time, random, struct, threading, signal
import logging

import protocol
import construct
from canbus import CANProtocol

def p(x): return struct.pack('B',x)


#commandstructure: command + led + args
#normally bytes.
#time is always 2 byte (short) in milliseconds (big endian, 0-65535)
#r, g, b is one byte color (0-255)
COMMANDS = {
    'setMaster': struct.pack('B', 101),#struct(code+led+master)
    'setColorRGB': struct.pack('B', 102),#struct(code+led+r+g+b)
    'fadeToColor': struct.pack('B', 103),#struct(code+led+time+r+g+b)
    'randomColor': struct.pack('B', 104),#struct(code+led+time)
    'randomFading': struct.pack('B', 105),#struct(code+led+time)
    'strobe': struct.pack('B', 106),#struct(code+led+timeoff+timetotal)
    'cycle': struct.pack('B', 107),#struct(code+0+time)
    'cycleFade': struct.pack('B', 108),#struct(code+0+time)
    'setColorHSV': struct.pack('B', 109),#struct(code+led+h(2byte: 0-360)+s+v)
}

class Sender():
    def __init__(self, host='10.43.100.112', port=23):
        self.LED1 = 0b0001
        self.LED2 = 0b0010
        self.LED3 = 0b0100
        self.LED4 = 0b1000
        self.LEDALL = 0b1111
        self.host = host
        self.port = port
        self._connManager = ConnectionManager(host, port)
        self._connManager.start()
        self.protocolArne = CANProtocol()
        time.sleep(0.5)
        
        self.baseContainer = construct.Container(
                    frametype = 'CAN_MSG',
                    priority = 'REGULAR',
                    subnet = 'ZERO',
                    sender = 'ADDR_GW0'
        )
        self.ledBaseContainer = self.baseContainer
        self.ledBaseContainer.update(
            construct.Container(
                protocol = 'LED',
                receiver = 'ADDR_LED'
            )
        )
        self.lightBaseContainer = self.baseContainer
        self.lightBaseContainer.update(
            construct.Container(
                protocol = 'LIGHT',
                receiver = 'ADDR_LIGHT'
            )
        )

    def sendMessage(self,container):
        ret = 0
        payload = ''
        
        try:
            payload = protocol.gw_msg.build(container)
        except Exception,e:
            logging.warn('Exception when building container: %s'%str(e))
            ret = 1

        hexdump = Helper.hexdump(payload)
        bindump = Helper.bindump(payload)
        
        logging.debug('Attempting to send container\n%s\n' % str(container)\
                        +'Hex content: %s\n' % hexdump\
                        + 'Binary content: %s' % bindump)
        self._connManager.send(payload)
        
    def forceReconnect(self):
        self._connManager.disconnect()
        
    def setMaster(self, led, master):
        """Set master for LED"""
        logging.info("setting master for led %d to %d"%(led,master))
        self._connManager.send(self.protocolArne.setMaster(master, led=led))
        #self._connManager.send(COMMANDS['setMaster'] + struct.pack('B', led) + struct.pack('B', master))
        
    def setAllMaster(self, master):
        """Set master for LED"""
        logging.info("setting master for all leds to %d"%(master))
        self._connManager.send(self.protocolArne.setMaster(master))

    def getColorRGB(self, led):
        """Get current color of given LED from Node"""
        cont = self.baseContainer
        cont.update(construct.Container(
                mode = 'GETCOLOR',
                length = 2,
                leds = led,
                colormode = 'RGB',
                time = 10,
            )
        )
        callbackEvent = threading.Event()
        var = {}
        var['response'] = "timeout"
        def callback(container):
            if container.leds == led:
                var['response'] = container
                callbackEvent.set()
            else:
                self._connManager.regGetColorCallback(callback)
        self._connManager.regGetColorCallback(callback)
        self._connManager.sendContainer(cont)
        callbackEvent.wait(timeout=5)
        if callbackEvent.isSet():
            print "RGB: %d|%d|%d"%(var['response'].color1,var['response'].color2,var['response'].color3)
        else:
            print "Get color request timed out!"
        return var['response']

    def setColorRGB(self, led, r, g, b):
        """Set permanent RGB color for LED to given RGB (0-255)."""
        logging.info("setting RGB color of led %d %03d|%03d|%03d"%(led,r,g,b))
        cont = self.baseContainer
        cont.update(construct.Container(
                mode = 'COLOR',
                length = 7,
                leds = led,
                colormode = 'RGB',
                time1 = 0,
                color1 = r,
                color2 = g,
                color3 = b,
            )
        )
        self._connManager.sendContainer(cont)
        #self._connManager.send(self.protocolArne.setColorRGB(0, r, g, b, led=led))
        #self._connManager.send(COMMANDS['setColorRGB'] + struct.pack('B', led) + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b))

    def setColorHSV(self, led, h, s, v):
        """Set permanent HSV color for LED to given HSV (H: 0-359, S+V: 0-255)."""
        logging.info("setting HSV color of led %d %03d|%03d|%03d"%(led,h,s,v))
        self._connManager.send(COMMANDS['setColorHSV'] + struct.pack('B', led) + struct.pack('>H', h) + struct.pack('B', s) + struct.pack('B', v))

    def fadeToColor(self, led, millis, r, g, b):
        """Fade LED to given RGB (0-255) in given time (0-65535)."""
        logging.info("fade to color %03d|%03d|%03d in %.3f seconds"%(r,g,b,millis/1000.0))
        self._connManager.send(COMMANDS['fadeToColor'] + struct.pack('B', led) + struct.pack('>H', millis) + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b))

    def white(self):
        """Shortcut to set LEDs permanent white (full brightness)"""
        self.setColorRGB(self.LEDALL, r=255, g=255, b=255)

    def black(self):
        """Shortcut to set LEDs permanent dark"""
        self.setColorRGB(self.LEDALL, r=0, g=0, b=0)
        
    def police(self, sleep=0.05):
        """Start Kotzmode. Interrupt with Ctrl+C"""
        while True:
            self.setColorRGB(self.LEDALL,0,0,0)
            for i in range(0,2):
                self.setColorRGB(self.LED1,0,0,128)
                self.setColorRGB(self.LED3,0,0,128)
                self.setColorRGB(self.LED4,0,0,255)
                time.sleep(sleep)
                self.setColorRGB(self.LED1,0,0,0)
                self.setColorRGB(self.LED3,0,0,0)
                self.setColorRGB(self.LED4,0,0,0)
                time.sleep(sleep)
            time.sleep(sleep*8)
            for i in range(0,2):
                self.setColorRGB(0b0001,0,0,128)
                self.setColorRGB(0b0100,0,0,128)
                self.setColorRGB(0b0010,255,0,0)
                time.sleep(sleep)
                self.setColorRGB(0b0001,0,0,0)
                self.setColorRGB(0b0100,0,0,0)
                self.setColorRGB(0b0010,0,0,0)
                time.sleep(sleep)
            time.sleep(sleep*8)

    def police_old(self,sleep=0.1):
        """Start another Kotzmode. Interrupt with Ctrl+C"""
        self.setAllMaster(0)
        while True:
            for i in range(0,2):
                self.setColorRGB(self.LEDALL,255,0,0)
                time.sleep(sleep)
                self.setColorRGB(self.LEDALL,0,0,255)
                time.sleep(sleep)
            self.setColorRGB(self.LEDALL,0,0,0)
            time.sleep(sleep/2)
            for i in range(0,2):
                self.setColorRGB(self.LEDALL,255,0,0)
                time.sleep(sleep)
                self.setColorRGB(self.LEDALL,0,0,255)
                time.sleep(sleep)
            self.setColorRGB(self.LEDALL,255,255,255)
            time.sleep(sleep/2)
    
    def strobe(self, led, time=80, r=255, g=255, b=255, factor=5):
        """Start strobemode
        
        params:
        time: total time of a cycle (millis_on = millis_total-millis_off)
        factor: time/factor = time on in one cycle
        r, g, b: color
        """
        cont = self.baseContainer
        cont.update(construct.Container(
                mode = 'STROBE',
                length = 8,
                leds = led,
                colormode = 'RGB',
                time1 = time,
                color1 = r,
                color2 = g,
                color3 = b,
                factor = factor,
            )
        )
        self._connManager.sendContainer(cont)

    def randomFading(self, led, millis=50):
        """Start automatic fading mode.
        
        params:
        led: led to fade
        millis: time between 2 fading steps"""
        self._connManager.send(COMMANDS['randomFading'] + struct.pack('B', led) + struct.pack('>H', millis))

    def randomColor(self, led, millis=1000):
        """Set all sleep milliseconds a new random color.
        
        params:
        sleep: sleeptime between 2 colors in milliseconds"""
        self._connManager.send(COMMANDS['randomColor'] + struct.pack('B', led) + struct.pack('>H', millis))

    def cycle(self, millis=300):
        """Cycle colors around every millis milliseconds"""
        self._connManager.send(self.protocolArne.cycle(millis))
        #self._connManager.send(COMMANDS['cycle'] + struct.pack('B', 0) + struct.pack('>H', millis))
        
    def runningLight(self, millis=100, r=0, g=0, b=255):
        """Create a light with given color that runs in circles"""
        self.setColorRGB(self.LEDALL,0,0,0)
        self.setColorRGB(self.LED1,r,g,b)
        self.cycle(millis)


    def switchLight(self, room, light, on=True):
        """Turn light On and Off"""
        # remapping - can be removed in next release
        if room == 2:
            if light == 1:
                lights = 0b00000001
            elif light == 2:
                lights = 0b00000010
        elif room == 3:
                lights = 0b00000100
        elif room == 4:
                lights = 0b00001000
        elif room == 5:
            if light == 1:
                lights = 0b00010000
            elif light == 2:
                lights = 0b00100000
        data_container = construct.Container(
            lights = lights,
            status = 'ON' if on else 'OFF'
        )
        #cont = self.lightBaseContainer
        #cont.update( construct.Container( can_msg_data = data_container ))
        #self._connManager.sendContainer(cont)

    def ping(self,times=4,timeout=4,receiver='ADDR_LED',numPongs=1):
        """Ping the CAN-Nodes"""
        pingContainer = construct.Container(
                    frametype = 'CAN_MSG',
                    priority = 'REGULAR',
                    subnet = 'ZERO',
                    protocol = 'PING',
                    receiver = receiver,
                    sender = 'ADDR_GW',
                    length = 1,
                    data = [0xFF],
        )
        for i in range(times):
            callbackEvent = threading.Event()
            var = {}
            var['numPongs'] = numPongs
            var['pongContainers'] = []
            def callback(container):
                var['pongContainers'].append(container)
                var['numPongs'] -= 1
                if var['numPongs'] > 0:
                    self._connManager.regPongCallback(callback)
                else:
                    callbackEvent.set()
            self._connManager.regPongCallback(callback)
            self._connManager.sendContainer(pingContainer)
            startTime = time.time()
            callbackEvent.wait(timeout=timeout)
            rtt = time.time() - startTime
            if callbackEvent.isSet():
                for cont in var['pongContainers']:
                    print "#%d received pong from %s. RTT %.4f seconds, can_time is %s"%(i,cont['sender'],rtt,cont['can_time'])
            else:
                print "#%d ping timeout"%i
            callbackEvent.clear()
    
    def testConnection(self):
        while True:
            self.setColorRGB(s.LEDALL,r=random.randint(0,255), g=random.randint(0,255), b=random.randint(0,255))
            time.sleep(1)

#    def fadeSoftRandom(self,sleep=0.1,minchange=1,maxchange=7):
#        """Start automatic fading mode. Fade in software, much networktraffic - don't use. Interrupt with Ctrl+C
#        
#        params:
#        sleep: waiting time between 2 fadingsteps in seconds
#        minchange: minimum stepsize
#        maxchange: maximum stepsize"""
#        col = [random.randrange(0,255), random.randrange(0,255), random.randrange(0,255)]
#        change = [random.randrange(minchange, maxchange), random.randrange(minchange, maxchange), random.randrange(minchange, maxchange)]
#        while True:
#            for i in range(0,3):
#                col[i] += change[i]
#                if col[i] > 254:
#                    col[i] = 254
#                    change[i] = random.randrange(minchange, maxchange)*-1
#                elif col[i] < 0:
#                    col[i] = 0
#                    change[i] = random.randrange(minchange, maxchange)
#            self.setColorRGB(col[0],col[1],col[2])
#            time.sleep(sleep)

    def stop(self):
        """Stop the Sender. Close all networkconnections and stop."""
        logging.debug('Received stop...')
        self._connManager.stop()
        self._connManager.join()


class ConnectionManager(threading.Thread):
    def __init__(self,  host, port):
        super(ConnectionManager, self).__init__()
        self.host = host
        self.port = port
        self.connected = False
        self.sendLock = threading.Lock()
        self.stopped = False
        self.lastReceivedPlain = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.daemon = True
        self.ping = False
        self.pongCallbacks = []
        self.getColorCallbacks = []
        self.pingContainer = construct.Container(
                    frametype = 'CAN_MSG',
                    priority = 'REGULAR',
                    subnet = 'ZERO',
                    protocol = 'PING',
                    receiver = 'ADDR_BC',
                    sender = 'ADDR_GW',
                    length = 1,
                    data = [0xFF],
        )
    
    def run(self):
        print 'ConnectionManager started. Trying to connect...'
        logging.info('ConnectionManager started. Trying to connect...')
        while not self.stopped:
            if not self.connected:
                self.tryconnect()
            else:
                try:
                    if self.ping:
                        self.sendContainer(self.pingContainer, log=False)
                    received = None
                    received = self.sock.recv(4096)
                    if not self.stopped:
                        if received:
                            logging.debug("received unicode: %s"%str(received))
                            logging.debug("received hex: %s"%Helper.hexdump(received))
                            for container in protocol.PacketHandler().parse(received):
                                logging.debug('Received container %s'%str(container))
                                try:
                                    if container['frametype'] == 'CAN_MSG':
                                        if container['protocol'] == 'PONG':
                                            for i in range(len(self.pongCallbacks)):
                                                cb = self.pongCallbacks.pop()
                                                cb(container)
                                        elif container['protocol'] == 'LED':
                                            if container['mode'] == 'GETCOLORRESPONSE':
                                                for i in range(len(self.getColorCallbacks)):
                                                    cb = self.getColorCallbacks.pop()
                                                    cb(container)
                                except Exception, e:
                                    logging.debug('exception when interpreting container: %s'%str(e))
                                    logging.exception(e)
                        else:
                            self.connectionReset()
                except socket.timeout, e:
                    pass
                except Exception, e:
                    logging.debug('in statechecker exception: %s'%str(e))
                    logging.exception(e)
                    self.connectionReset()
        logging.info('Closing connection...')
        try:
            self.stop()
        except Exception, e:
            pass
        logging.info('Connection closed, ConnectionManager stopped')
    
    def connectionReset(self):
        logging.debug("connection reset")
        print "Connection lost. Reconnecting..."
        self.sendLock.acquire(False)
        self.sendLock.release()
        self.sendLock.acquire()
        self.connected = False
        self.lastReceived = 'Connection error'
        
    def setEnablePing(self, ping):
        self.ping = ping

    def regPongCallback(self, cb):
        self.pongCallbacks.append(cb)

    def regGetColorCallback(self, cb):
        self.getColorCallbacks.append(cb)
    
    def connect(self):
        self.sendLock.acquire(False)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1)
        self.sock.connect((self.host, self.port))
        self.connected = True
        logging.debug("connection established")
        print "Connected to %s:%d"%(self.host,self.port)
        self.sendLock.release()
    
    def stop(self):
        self.stopped = True
        self.disconnect()
    
    def disconnect(self):
        self.sendLock.acquire(False)
        self.sock.close()
        logging.debug("disconnect")
        self.connected = False
    
    def tryconnect(self):
        self.sendLock.acquire(False)
        try:
            self.disconnect()
        except:
            pass
        logging.debug("Trying to connect...")
        while not self.connected and not self.stopped:
            try:
                self.connect()
                logging.info("Connected to %s:%d"%(self.host,self.port))
            except socket.timeout:
                pass
            except Exception, e:
                logging.info(e)
                time.sleep(0.1)
                logging.debug("Trying to connect...")
                
    def sendContainer(self,container,log=True):
        ret = 0
        payload = ''
        
        try:
            payload = protocol.gw_msg.build(container)
        except Exception,e:
            logging.error('Exception when building container: %s'%str(e))
            logging.exception(e)
            ret = 1

        #hexdump = Helper.hexdump(payload)
        #bindump = Helper.bindump(payload)
        if log:
            logging.debug('Sending container\n%s\n' % str(container))
        self.send(payload, log)

    def send(self, msg, log=True):
        if self.connected:
            if log:
                logging.debug("waiting for sendLock...")
            self.sendLock.acquire()
            if log:
                logging.debug("sendLock acquired")
                logging.info("sending unicode \t%s"%msg)
            hexmsg = ''
            binmsg = ''
            for c in msg:
                binmsg += Helper.format8bit(bin(struct.unpack('B',c)[0])) + ' '
                hexmsg += hex(struct.unpack('B',c)[0]) + ' '
            if log:
                logging.info("sending binary %s"%binmsg)
                logging.info("sending hex %s"%Helper.hexdump(msg))
            try:
                self.sock.sendall(msg)
            except Exception, e:
                logging.warn('Exception when sending: %s'%str(e))
                print "Connection error. Reconnecting..."
                self.sendLock.release()
                self.connectionReset()
            self.sendLock.release()
        else:
            logging.warn("Not sent. Socket not connected")

class Helper:
    @staticmethod
    def format8bit(binstr):
        return ('0'*(8-len(binstr[2:]))) + binstr[2:]

    @staticmethod
    def hexdump(string):
        hexdump = ''
        for char in string:
            hexdump += "0x%02x " % int(ord(char))
        return hexdump

    @staticmethod
    def bindump(string):
        bindump = ''
        for i,char in enumerate(string):
            bindump += "%d|%s|" % (i,Helper.binx(ord(char),8))
        return bindump

    @staticmethod
    def binx(x, digits=0):
        oct2bin = ['000','001','010','011','100','101','110','111'] 
        binstring = [oct2bin[int(n)] for n in oct(x)] 
        return ''.join(binstring).lstrip('0').zfill(digits)

def main():
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%d.%m.%y %H:%M:%s',
#                        filename='sender.log',
                        filemode='a')
    #logging.critical("Critical")
    #logging.error("Error")
    #logging.warning("Warning")
    #logging.info("Info")
    #logging.debug("Debug")
    
    global s
    s = Sender()

    #######################
    #fancy startup shit (history, tabcompletion & Co)
    #######################
    import atexit
    import os
    import readline
    import rlcompleter
    historyPath = os.path.expanduser("~/.pyhistory")
    historyTmp = os.path.expanduser("~/.pyhisttmp.py")
    endMarkerStr= "# # # histDUMP # # #"
    saveMacro= "import readline; readline.write_history_file('"+historyTmp+"'); \
        print '####>>>>>>>>>>'; print ''.join(filter(lambda lineP: \
        not lineP.strip().endswith('"+endMarkerStr+"'),  \
        open('"+historyTmp+"').readlines())[:])+'####<<<<<<<<<<'"+endMarkerStr
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('\C-w: "'+saveMacro+'"')
    def save_history(historyPath=historyPath, endMarkerStr=endMarkerStr):
        import readline
        readline.write_history_file(historyPath)
        # Now filter out those line containing the saveMacro
        lines= filter(lambda lineP, endMarkerStr=endMarkerStr:
                          not lineP.strip().endswith(endMarkerStr), open(historyPath).readlines())
        open(historyPath, 'w+').write(''.join(lines))
    if os.path.exists(historyPath):
        readline.read_history_file(historyPath)
    atexit.register(save_history)

    del os, atexit, readline, rlcompleter, save_history, historyPath
    del historyTmp, endMarkerStr, saveMacro
    #######################
    #end fancy startup shit
    #######################

    import code
    code.InteractiveConsole(locals=globals()).interact("s is your Sender! try 's.police()'")
    print "Stopping network daemon..."
    s.stop()
    print "Stopped. Exiting..."
if __name__ == "__main__":
    main()
