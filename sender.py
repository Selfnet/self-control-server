import socket, time, random, struct, threading, signal
import logging

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
    def __init__(self, host='10.43.100.111', port=23):
        self.host = host
        self.port = port
        self.connManager = ConnectionManager(host, port)
        self.connManager.start()
        
    def setMaster(self, led, master):
        """Set master for LED"""
        logging.info("setting master for led %d to %d"%(led,master))
        self.connManager.send(COMMANDS['setMaster'] + struct.pack('B', led) + struct.pack('B', master))
        
    def setAllMaster(self, master):
        """Set master for LED"""
        logging.info("setting master all leds to %d"%(master))
        for i in range(0,4):
            self.setMaster(i, master)

    def setColorRGB(self, led, r, g, b):
        """Set permanent RGB color for LED to given RGB (0-255)."""
        logging.info("setting RGB color of led %d %03d|%03d|%03d"%(led,r,g,b))
        self.connManager.send(COMMANDS['setColorRGB'] + struct.pack('B', led) + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b))

    def setColorHSV(self, led, h, s, v):
        """Set permanent HSV color for LED to given HSV (H: 0-359, S+V: 0-255)."""
        logging.info("setting HSV color of led %d %03d|%03d|%03d"%(led,h,s,v))
        self.connManager.send(COMMANDS['setColorHSV'] + struct.pack('B', led) + struct.pack('>H', h) + struct.pack('B', s) + struct.pack('B', v))

    def setAllColor(self, r, g, b):
        """Set master for LED"""
        logging.info("setting all leds to %03d|%03d|%03d"%(r,g,b))
        for i in range(0,4):
            self.setColorRGB(i, r, g, b)

    def fadeToColor(self, led, millis, r, g, b):
        """Fade LED to given RGB (0-255) in given time (0-65535)."""
        logging.info("fade to color %03d|%03d|%03d in %.3f seconds"%(r,g,b,millis/1000.0))
        self.connManager.send(COMMANDS['fadeToColor'] + struct.pack('B', led) + struct.pack('>H', millis) + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b))

    def white(self):
        """Shortcut to set LEDs permanent white (full brightness)"""
        self.setColorRGB(254, 254, 254)

    def black(self):
        """Shortcut to set LEDs permanent dark"""
        self.setColorRGB(0, 0, 0)
        
    def police(self, sleep=0.05):
        """Start Kotzmode. Interrupt with Ctrl+C"""
        while True:
            self.setColorRGB(0,0,0,0)
            self.setColorRGB(0,0,0,1)
            self.setColorRGB(0,0,0,2)
            self.setColorRGB(0,0,0,3)
            for i in range(0,2):
                self.setColorRGB(0,0,255,0)
                self.setColorRGB(0,0,255,2)
                self.setColorRGB(0,0,255,3)
                time.sleep(sleep)
                self.setColorRGB(0,0,0,0)
                self.setColorRGB(0,0,0,2)
                self.setColorRGB(0,0,0,3)
                time.sleep(sleep)
            time.sleep(sleep*5)
            for i in range(0,2):
                self.setColorRGB(255,0,0,0)
                self.setColorRGB(255,0,0,2)
                self.setColorRGB(255,0,0,1)
                time.sleep(sleep)
                self.setColorRGB(0,0,0,0)
                self.setColorRGB(0,0,0,2)
                self.setColorRGB(0,0,0,1)
                time.sleep(sleep)
            time.sleep(sleep*5)

    def police_old(self):
        """Start another Kotzmode. Interrupt with Ctrl+C"""
        while True:
            for i in range(0,2):
                self.setColorRGB(255,0,0)
                time.sleep(0.1)
                self.setColorRGB(0,0,255)
                time.sleep(0.1)
            self.setColorRGB(0,0,0)
            time.sleep(0.05)
            for i in range(0,2):
                self.setColorRGB(255,0,0)
                time.sleep(0.1)
                self.setColorRGB(0,0,255)
                time.sleep(0.1)
            self.setColorRGB(255,255,255)
            time.sleep(0.05)
    
    def strobe(self, led, millisoff=80, millistotal=100):
        """Start strobemode
        
        params:
        millisoff: light off for this time
        millistotal: total time of a cycle (millison = millistotal-millisoff)"""
        self.connManager.send(COMMANDS['strobe'] + struct.pack('B', led) + struct.pack('>H', millisoff) + struct.pack('>H', millistotal))

    def randomFading(self, led, millis=50):
        """Start automatic fading mode.
        
        params:
        led: led to fade
        millis: time between 2 fading steps"""
        self.connManager.send(COMMANDS['randomFading'] + struct.pack('B', led) + struct.pack('>H', millis))

    def randomColor(self, led, millis=1000):
        """Set all sleep milliseconds a new random color.
        
        params:
        sleep: sleeptime between 2 colors in milliseconds"""
        self.connManager.send(COMMANDS['randomColor'] + struct.pack('B', led) + struct.pack('>H', millis))

    def cycle(self, millis=300):
        """Cycle colors around every millis milliseconds"""
        self.connManager.send(COMMANDS['cycle'] + struct.pack('B', 0) + struct.pack('>H', millis))

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

#    def light(self, state, lightnr=1):
#        """Set lightnr (1 = cold bright light) to given state: 0 (off) or 1 (on)"""
#        state = state + 1
#        self.connManager.send(COMMANDS['light'] + struct.pack('B', lightnr) + struct.pack('B', state))

    def stop(self):
        """Stop the Sender. Close all networkconnections and stop."""
        logging.debug('Received stop...')
        self.connManager.stop()
        self.connManager.join()

class ConnectionManager(threading.Thread):
    def __init__(self,  host, port):
        super(ConnectionManager, self).__init__()
        self.host = host
        self.port = port
        self.connected = False
        self.sendLock = threading.Lock()
        self.recvLock = threading.Lock()
        self.recvLock.acquire()
        self.stopped = False
        self.lastReceived = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def run(self):
        print 'ConnectionManager started. Trying to connect...'
        logging.info('ConnectionManager started. Trying to connect...')
        while not self.stopped:
            if not self.connected:
                self.tryconnect()
            else:
                self.recvLock.acquire(False)
                try:
                    self.send(struct.pack('B', 1), log=False)
                    self.lastReceived = 'untouched'
                    self.lastReceived = self.sock.recv(4096)
                    if not self.stopped:
                        if self.lastReceived:
                            logging.debug("received: %s"%self.lastReceived)
                            self.recvLock.release()
                            self.recvLock.acquire()
                        else:
                            self.connectionReset()
                except socket.timeout, e:
                    pass
                except Exception, e:
                    logging.debug('in statechecker exception: %s'%str(e))
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
        self.recvLock.release()
        self.recvLock.acquire()

    def recv(self):
        self.recvLock.acquire()
        self.recvLock.release()
        return self.lastReceived
    
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

    def send(self, msg, log=True):
        if self.connected:
            if log:
                logging.debug("waiting for sendLock...")
            self.sendLock.acquire()
            if log:
                logging.debug("sendLock acquired")
                logging.info("sending unicode %s"%msg)
            binmsg = ''
            for c in msg:
                binmsg += Helper.format8bit(bin(struct.unpack('B',c)[0])) + ' '
            if log:
                logging.info("sending binary %s"%binmsg)
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

def main():
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%d.%m.%y %H:%M:%s',
                        filename='sender.log',
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
