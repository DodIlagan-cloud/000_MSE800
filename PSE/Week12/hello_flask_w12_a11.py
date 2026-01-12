"""
W12 A1.1 - Flask test
Eduardo JR Ilagan
"""
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_flask():
    """Flask test - Hello"""
    return "<p>Hello, Flask!</p>"


@app.route("/lili")
def hello_lili():
    """Flask test - Lili"""
    return "<p>Hello, Flask! Lili</p>"

if __name__ == '__main__':
    app.run (debug=True)
