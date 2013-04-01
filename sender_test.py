import protocol
import construct
import sender
import logging

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
                    subnet = 'NOC',
                    protocol = 'LED',
                    receiver = 'ADDR_LED',
                    sender = 'ADDR_GW',
                    length = 3,
                    mode = 'MASTER',
                    leds = [0,0,1,0],
                    colormode = 'RGB',
                    led = 2,
                    )



s = sender.Sender()
s.sendMessage(container)


#print container

#payload = protocol.gw_msg.build(container)

#hexdump = ''
#for char in payload:
#    hexdump += "\\x%02x" % int(ord(char))
#print hexdump

#bindump = ''
#for i,char in enumerate(payload):
#    bindump += "%d|%s|" % (i,binx(ord(char),8))
#print bindump

#container = protocol.gw_msg.parse(payload)

#print container
