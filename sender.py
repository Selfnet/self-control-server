import socket, time, random, struct

#commands: binary -> commandbyte + args
COMMANDS = {
    'setColor': struct.pack('B', 100),#struct(100+r+g+b) with r,g,b in range 0-255
    'fadeToColor': struct.pack('B', 101),#struct(101+r+g+b+time) with r,g,b in 0-255, time in range 0-255 with 1 = 0.1sec
}

class Sender():
    def __init__(self, connect=True, host='10.43.100.111', port=23):
        self.host = host
        self.port = port
        
        if connect:
            self.connect()
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print "received:", self.sock.recv(1024)
        
    def disconnect(self):
        self.sock.close()
    
    def reconnect(self):
        try:
            self.disconnect()
        except:
            pass
        self.tryconnect()
    
    def tryconnect(self):
        try:
            self.disconnect()
        except:
            pass
        connected = False
        while not connected:
            print "Trying to connect..."
            try:
                self.connect()
                connected = True
                print "Connected"
            except Exception, e:
                print e

    def send(self, msg):
        self.sock.sendall(msg)

    def setColor(self, r,g,b):
        print "setting color %03d|%03d|%03d"%(r,g,b)
        self.sock.sendall(COMMANDS['setColor'] + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b))
    
    def fadeToColor(self, r, g, b, duration):
        print "fade to color %03d|%03d|%03d in %.1f seconds"%(r,g,b,duration*0.1)
        self.sock.sendall(COMMANDS['fadeToColor'] + struct.pack('B', r) + struct.pack('B', g) + struct.pack('B', b) + struct.pack('B', duration))
        time.sleep((duration+2)*0.1)
        #self.sock.recv(32)
        print "fading finished"

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
            time.sleep(0.1)
            for i in range(0,2):
                self.setColor(255,0,0)
                time.sleep(0.1)
                self.setColor(0,0,255)
                time.sleep(0.1)
            self.setColor(255,255,255)
            time.sleep(0.1)
    
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
