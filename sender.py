import socket, time, random, struct, threading, signal
import logging

#commands: binary -> commandbyte + args
COMMANDS = {
    'setColor': struct.pack('B', 100),#struct(100+r+g+b) with r,g,b in range 0-255
    'fadeToColor': struct.pack('B', 101),#struct(101+r+g+b+time) with r,g,b in 0-255, time in range 0-255 with 1 = 0.1sec
    'light': struct.pack('B', 102),#struct(102+lightnr+state) with state = [0|1]
    'configureAutofade': struct.pack('B', 103),#struct(103+time) with 2bytes time in milliseconds
    'setSmoothfadeTime': struct.pack('B', 104),#struct(104+time) with 2bytes time in milliseconds
}

# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%d.%m.%y %H:%M:%s',
                    filename='sender.log',
                    filemode='w')
#logging.critical("Critical")
#logging.error("Error")
#logging.warning("Warning")
#logging.info("Info")
#logging.debug("Debug")

class Sender():
    def __init__(self, host='10.43.100.111', port=23):
        self.host = host
        self.port = port
        #signal.signal(signal.SIGTERM, self.signal_handler)
        for i in [x for x in dir(signal) if x.startswith("SIG")]:
            try:
                signum = getattr(signal,i)
                signal.signal(signum,self.signal_handler)
            except RuntimeError,m:
                print "Skipping %s"%i
            except ValueError,m:
                print "Skipping %s"%i
        self.connManager = ConnectionManager(host, port)
        self.connManager.start()

    def setColor(self, r,g,b):
        logging.info("setting color %03d|%03d|%03d"%(r,g,b))
        self.connManager.send(COMMANDS['setColor'] + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b))
    
    def fadeToColor(self, r, g, b, duration):
        logging.info("fade to color %03d|%03d|%03d in %.1f seconds"%(r,g,b,duration*0.1))
        self.connManager.send(COMMANDS['fadeToColor'] + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b) + struct.pack('B', duration))
        time.sleep((duration+2)*0.1)
        logging.debug("received: %s"%self.connManager.recv())

    def light(self, state, lightnr=1):
        state = state + 1
        self.connManager.send(COMMANDS['light'] + struct.pack('B', lightnr) + struct.pack('B', state))

    def configureAutofade(self, time):
        self.connManager.send(COMMANDS['configureAutofade'] + struct.pack('>H', time))

    def setSmoothfadeTime(self, time):
        self.connManager.send(COMMANDS['setSmoothfadeTime'] + struct.pack('>H', time))

    def white(self):
        self.setColor(254, 254, 254)

    def black(self):
        self.setColor(0, 0, 0)
        
    def police(self):
        while True:
            for i in range(0,2):
                self.setColor(255,0,0)
                time.sleep(0.1)
                self.setColor(0,0,255)
                time.sleep(0.1)
            self.setColor(0,0,0)
            time.sleep(0.08)
            for i in range(0,2):
                self.setColor(255,0,0)
                time.sleep(0.1)
                self.setColor(0,0,255)
                time.sleep(0.1)
            self.setColor(255,255,255)
            time.sleep(0.08)
            
    def police2(self):
        while True:
            for i in range(0,2):
                self.setColor(255,255,0)
                time.sleep(0.1)
                self.setColor(0,255,0)
                time.sleep(0.1)
            self.setColor(0,0,0)
            time.sleep(0.05)
            for i in range(0,2):
                self.setColor(255,255,0)
                time.sleep(0.1)
                self.setColor(0,255,0)
                time.sleep(0.1)
            self.setColor(255,255,255)
            time.sleep(0.05)
    
    def strobe(self,sleep=0.05):
        while True:
            self.setColor(255,255,255)
            time.sleep(sleep*0.5)
            self.setColor(0,0,0)
            time.sleep(sleep)
    
    def fadeSoftRandom(self,sleep=0.1,minchange=1,maxchange=7):
        col = [random.randrange(0,255), random.randrange(0,255), random.randrange(0,255)]
        change = [random.randrange(minchange, maxchange), random.randrange(minchange, maxchange), random.randrange(minchange, maxchange)]
        while True:
            for i in range(0,3):
                col[i] += change[i]
                if col[i] > 254:
                    col[i] = 254
                    change[i] = random.randrange(minchange, maxchange)*-1
                elif col[i] < 0:
                    col[i] = 0
                    change[i] = random.randrange(minchange, maxchange)
            self.setColor(col[0],col[1],col[2])
            time.sleep(sleep)
            
    def fadeHardRandom(self,mintime=1,maxtime=255):
        while True:
            self.fadeToColor(random.randrange(0,255), random.randrange(0,255), random.randrange(0,255), random.randrange(mintime,maxtime))

    def randomColor(self, sleep=1):
        while True:
            r = random.randrange(0,255)
            g = random.randrange(0,255)
            b = random.randrange(0,255)
            self.setColor(r, g, b)
            time.sleep(sleep)
            
    def stop(self):
        self.connManager.stop()

    def signal_handler(signal, frame):
            print 'signal %s received'%signal
            self.stop()

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
        while not self.stopped:
            if not self.connected:
                self.tryconnect()
            else:
                self.recvLock.acquire(False)
                try:
                    self.lastReceived = 'untouched'
                    self.lastReceived = self.sock.recv(4096)
                    if self.lastReceived:
                        logging.debug("received: %s"%self.lastReceived)
                        self.recvLock.release()
                        self.recvLock.acquire()
                    else:
                        self.connectionReset()
                except socket.timeout, e:
                    logging.debug(e)
                except Exception, e:
                    logging.debug(e)
                    self.connectionReset()
        logging.info('Connection closed, ConnectionManager stopped')
    
    def connectionReset(self):
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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.connected = True
        self.sendLock.release()
    
    def stop(self):
        self.stopped = True
        self.disconnect()
    
    def disconnect(self):
        self.sendLock.acquire(False)
        self.sock.close()
        self.connected = False
    
    def tryconnect(self):
        self.sendLock.acquire(False)
        self.sock.settimeout(1)
        try:
            self.disconnect()
        except:
            pass
        logging.debug("Trying to connect...")
        while not self.connected:
            try:
                self.connect()
                logging.info("Connected")
            except socket.timeout:
                pass
            except Exception, e:
                logging.info(e)
                time.sleep(0.1)
                logging.debug("Trying to connect...")
        self.sock.settimeout(0)
        self.sock.setblocking(True)

    def send(self, msg):
        logging.info("waiting for sendLock...")
        self.sendLock.acquire()
        logging.info("sendLock acquired")
        if self.connected:
            logging.info("sending unicode %s"%msg)
            binmsg = ''
            for c in msg:
                binmsg += Helper.format8bit(bin(struct.unpack('B',c)[0])) + ' '
            logging.info("sending binary %s"%binmsg)
            self.sock.sendall(msg)
        else:
            logging.warn("Not sent. Socket not connected")
        self.sendLock.release()

class Helper:
    @staticmethod
    def format8bit(binstr):
        return ('0'*(8-len(binstr[2:]))) + binstr[2:]
