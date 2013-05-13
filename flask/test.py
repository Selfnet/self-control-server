from flask import Flask, jsonify, render_template

import sender
app = Flask(__name__)

s = sender.Sender()


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/U2/LED/rgb/set/<int:red>/<int:green>/<int:blue>/")
def setLedColor(red,green,blue):
    s.setColorRGB(s.LEDALL, red, green, blue)
    return render_template('rgb.html', red=red, green=green, blue=blue)

@app.route("/U2/LED/rgb/get/<int:led>/")
def getLedColor(led):
    cont = s.getColorRGB(0x1 << led-1)
    return jsonify({'red':cont.color1, 'green':cont.color2, 'blue':cont.color3})

if __name__ == "__main__":
    app.run(host='0.0.0.0')
