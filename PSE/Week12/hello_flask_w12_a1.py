"""
W12 A1 - Flask test
Eduardo JR Ilagan
"""
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_flask():
    """Flask test"""
    return "<p>Hello, Flask!</p>"

if __name__ == '__main__':
    app.run (debug=True)
