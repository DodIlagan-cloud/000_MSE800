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


@app.route("/dod")
def hello_lili():
    """Flask test - dod"""
    return "<p>Hello, Flask! Dod</p>"

@app.route('/cal/<int:number>')
def show_square(number):
    """Flask test - Number"""
    return f"The square of {number} is {number**2}"

if __name__ == '__main__':
    app.run (debug=True)
