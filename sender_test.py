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
                    priority = 'REGULAR',
                    subnet = 'ZERO',
                    protocol = 'LED',
                    receiver = 'ADDR_LED',
                    sender = 'ADDR_GW',
                    mode = 'COLOR',
                    length = 7,
                    leds = [1,1,1,1],
                    colormode = 'RGB',
                    time1 = 0,
                    color1 = 255,
                    color2 = 255,
                    color3 = 255,
                    )


try:
    s = sender.Sender()
    #s.sendMessage(container)
    time.sleep(0.5)

#    while(1):
#        s.setAllColorRGB(0,0,0)
#        time.sleep(0.1)
#        s.setAllColorRGB(255,255,255)
#        time.sleep(0.1)

    while(1):
        rand_time = random.randint(60,240)
        time.sleep(rand_time)

        color = random.randint(0,255)
        container.color1 = color
        color = random.randint(0,255)
        container.color2 = color
        color = random.randint(0,255)
        container.color3 = color
        s.sendMessage(container)
        time.sleep(0.05)
        container.color1 = 0
        container.color2 = 0
        container.color3 = 0
        s.sendMessage(container)

#    while(1):
#        leds = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
#        for led in leds:
#            container.leds = led
#            color = random.randint(0,255)
#            container.color1 = color
#            color = random.randint(0,255)
#            container.color2 = color
#            color = random.randint(0,255)
#            container.color3 = color
#            s.sendMessage(container)
#            time.sleep(0.25)
except KeyboardInterrupt:
        print 'Keyboard Interrupt'

print 'Killing server crap'
time.sleep(2)
s.stop()
print 'Killed server crap'
