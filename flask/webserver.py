from flask import Flask, jsonify, render_template, abort

import BaseHTTPServer
import sender
import time
app = Flask(__name__)

__builtins__.s = sender.Sender()

__builtins__.lights = 0;

@app.route("/")
def index():
    return render_template('index.html')


@app.route("/U<int:room>/light/set/<int:light>/<int:on>/" , methods=['GET', 'POST'])
def switchLight(room,light,on):
    print room,light
    if 2 <= room <= 5:
        s.switchLight(room,light,on)
        return jsonify({'state':'ok'})
    return jsonify({'state':'error', 'error':'room not found'})

last_lights = {'time':0, 'lights':0}

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

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(8080)
    IOLoop.instance().start()

    #app.run(host='0.0.0.0', port=8080)
