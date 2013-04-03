import protocol
import construct
import sender
import logging, time
import random

def binx(x, digits=0): 
    oct2bin = ['000','001','010','011','100','101','110','111'] 
    binstring = [oct2bin[int(n)] for n in oct(x)] 
    return ''.join(binstring).lstrip('0').zfill(digits)

# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%d.%m.%y %H:%M:%s',
                    filename='sender.log',
                    filemode='a')

container = construct.Container(
                    frametype = 'CAN_MSG',
                    service = 'REGULAR',
                    subnet = 'ZERO',
                    protocol = 'LED',
                    receiver = 'ADDR_LED',
                    sender = 'ADDR_GW',
                    mode = 'FADE',
                    length = 7,
                    leds = [1,1,1,1],
                    colormode = 'RGB',
                    time = 3000,
                    color1 = 255,
                    color2 = 255,
                    color3 = 255,
                    )


try:
    s = sender.Sender()
    s.sendMessage(container)
    time.sleep(0.5)
    while(1):
        hue = random.randint(0,255)
        container.color1 = hue
        container.color3 = 255
        #s.sendMessage(container)
        time.sleep(3)
        container.color1 = hue
        container.color3 = 0
        #s.sendMessage(container)
        time.sleep(3)
except KeyboardInterrupt:
        print 'Keyboard Interrupt'

print 'Killing server crap'
time.sleep(2)
s.stop()
print 'Killed server crap'
