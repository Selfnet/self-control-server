from flask import Flask, jsonify, render_template, abort

import sender
app = Flask(__name__)

s = sender.Sender()

@app.route("/")
def index():
    return render_template('index.html')



@app.route("/U<int:room>/light/set/<int:light>/<int:on>/")
def switchLight(room,light,on):
    print room,light
    if 2 <= room <= 5:
        s.switchLight(room,light,on)
        return jsonify({'state':'ok'})
    return jsonify({'state':'error', 'error':'room not found'})


@app.route("/U2/LED/rgb/set/<int:led>/<int:red>/<int:green>/<int:blue>/")
def setLedColor(led,red,green,blue):
    s.setColorRGB(led, red, green, blue)
    return render_template('rgb.html', red=red, green=green, blue=blue)

@app.route("/U2/LED/rgb/get/<int:led>/")
def getLedColor(led):
    cont = s.getColorRGB(0x1 << led-1)
    if isinstance(cont, str):
        return "Gateway timeout", 504
    return jsonify({'red':cont.color1, 'green':cont.color2, 'blue':cont.color3})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
