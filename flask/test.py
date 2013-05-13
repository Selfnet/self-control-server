from flask import Flask

import sender
app = Flask(__name__)

s = sender.Sender()


@app.route("/")
def hello():
    return "Hello World!"

@app.route("/U2/LED/rgb/<int:red>/<int:green>/<int:blue>/")
def setLedColor(red,green,blue):
    s.setColorRGB(s.LEDALL,red,green,blue )
    return "asd"

if __name__ == "__main__":
    app.run()
