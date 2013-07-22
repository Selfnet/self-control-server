from flask import Flask, jsonify, render_template, abort

import BaseHTTPServer
import sender
import time
import subprocess

#falid state: off,on,start
pcs_u3 = [{'name':'tr01','status':'off','mac':'14:da:e9:de:d5:75','ip':'10.43.101.1'}, {'name':'tr02','status':'off','mac':'14:da:e9:de:d5:7A','ip':'10.43.102.1'}, 
            {'name':'tr03','status':'off','mac':'14:da:e9:de:d5:09','ip':'10.43.103.1'}, {'name':'tr04','status':'off','mac':'14:da:e9:de:d5:5c','ip':'10.43.104.1'},
            {'name':'tr05','status':'off','mac':'14:da:e9:de:d5:d4','ip':'10.43.105.1'}, {'name':'tr06','status':'off','mac':'14:da:e9:de:d5:7e','ip':'10.43.106.1'}, 
            {'name':'tr07','status':'off','mac':'14:da:e9:de:d4:df','ip':'10.43.107.1'}, {'name':'tr08','status':'off','mac':'4:da:e9:de:d6:27','ip':'10.43.108.1'}]

pcs_u4 = [{'name':'tr09','status':'off','mac':'14:da:e9:de:d5:82','ip':'10.43.109.1'}, {'name':'tr10','status':'off','mac':'14:da:e9:de:d5:70','ip':'10.43.110.1'}, 
            {'name':'tr11','status':'off','mac':'14:da:e9:de:d4:e0','ip':'10.43.111.1'}, {'name':'tr12','status':'off','mac':'14:da:e9:de:d5:79','ip':'10.43.112.1'},
            {'name':'tr13','status':'off','mac':'14:da:e9:de:d5:55','ip':'10.43.113.1'}, {'name':'tr14','status':'off','mac':'14:DA:E9:DE:D4:C4','ip':'10.43.114.1'}, 
            {'name':'tr15','status':'off','mac':'14:da:e9:de:d4:ed','ip':'10.43.115.1'}, {'name':'tr16','status':'off','mac':'14:da:e9:de:d5:0f','ip':'10.43.116.1'}]


def updateStatus():
    from threading import Timer

    def ping(ip):
        p = subprocess.Popen( ("ping -c1 %s" %(ip)).split(),
                          shell=False,
                          stdout=subprocess.PIPE)
        p.communicate()
        return p.returncode

    for pc in pcs_u3+pcs_u4:
        s = ping(pc['ip'])
        if s == 0: #online
            pc['status'] = 'on'
        elif s == 1: #offline
            pc['status'] = 'off'
    t = Timer(10.0, updateStatus)
    t.start()


app = Flask(__name__)

s = sender.Sender()
lights = 0;


@app.route("/")
def index():
    return render_template('index.html' , tab=0,  pcs_u4=pcs_u4 , pcs_u3=pcs_u3 )


@app.route("/wol/tr<int:tr>/")
def wake(tr):
    from subprocess import call
    for pc in pcs_u3+pcs_u4:
        if pc['name'] == 'tr%02d'%tr:
            mac = pc['mac']
            pc['status'] = 'start'
            break
    print 'waking up mac:',mac
    call(["/usr/bin/wakeonlan", mac])
    return render_template('index.html' , tab=1 , pcs_u4=pcs_u4 , pcs_u3=pcs_u3 )


@app.route("/U<int:room>/light/set/<int:light>/<int:on>/" , methods=['GET', 'POST'])
def switchLight(room,light,on):
    print room,light
    if 2 <= room <= 5:
        s.switchLight(room,light,on)
        return jsonify({'state':'ok'})
    return jsonify({'state':'error', 'error':'room not found'})

last_lights = {'time':0, 'lights':0}

@app.route("/lights/get/" , methods=['GET', 'POST'])
def checkLights():
    if last_lights['time'] < time.time()-10:
        last_lights['time'] = time.time()
        last_lights['lights'] = s.checkLight().can_msg_data.lights
    l = last_lights['lights']
    return jsonify({'state': l})

@app.route("/U<int:room>/light/get/<int:light>/" , methods=['GET', 'POST'])
def checkLight(room,light):
    print room,light
    if 2 <= room <= 5:
        if last_lights['time'] < time.time()-10:
            last_lights['time'] = time.time()
            last_lights['lights'] = s.checkLight().can_msg_data.lights
        l = last_lights['lights']
        if room == 2:
            if light == 1:
                return jsonify({'state': l & 0b01000000 > 0}) #u2 kalt
            else:
                return jsonify({'state': l & 0b10000000 > 0}) #u2 nich so kalt (aka warm)
        elif room == 3:
            return jsonify({'state': l & 0b00100000 > 0}) #u3
        elif room == 4:
            return jsonify({'state': l & 0b00000100 > 0})
        elif room == 5:
            if light == 1:
                return jsonify({'state': l & 0b00010000 > 0})
            else:
                return jsonify({'state': l & 0b00001000 > 0})
    print 'error',room,light,l
    return jsonify({'state':'error', 'error':'room not found'})



@app.route("/U2/LED/rgb/set/<int:led>/<int:red>/<int:green>/<int:blue>/" , methods=['GET', 'POST'])
def setLedColor(led,red,green,blue):
    s.setColorRGB(led, red, green, blue)
    return render_template('rgb.html', red=red, green=green, blue=blue)

last_leds = {'time':0, 'leds':0}

@app.route("/U2/LED/rgb/get/<int:led>/" , methods=['GET', 'POST'])
def getLedColor(led):
    if last_leds['time'] < time.time()-1:
        last_leds['time'] = time.time()
        last_leds['leds'] = s.getColorRGB(0x1 << led-1)
    cont = last_leds['leds']

    #return "Gateway timeout", 504 #currently broken
    print "received getcolor"
#    cont = s.getColorRGB(0x1 << led-1)
    if isinstance(cont, str):
        return "Gateway timeout", 504
    return jsonify({'red':cont.color1, 'green':cont.color2, 'blue':cont.color3})

if __name__ == "__main__":

    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop

    updateStatus()

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(8080)
    IOLoop.instance().start()

    #app.run(host='0.0.0.0', port=8080)
