"""
W12 A2 - Flask test
Develop a Wb Application to have Hyper link and 
load an image (from end user input) using Flask.

Eduardo JR Ilagan
"""
from flask import Flask, render_template, url_for

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

@app.route('/image')
def show_image():
    """Flask test - Number"""
    return render_template("sample.html")

if __name__ == '__main__':
    app.run (debug=True)
