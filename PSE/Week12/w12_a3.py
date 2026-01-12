"""
Week 12 - Activity 3-  Develop a web APP - Temperature Converter (Celsius , Fahrenheit ,  Kelvin )
Develop a web- APP to convert the temperature using the following table. (\frac{5}{9} => 5/9)
 
Conversion	Formula
Celsius -> Fahrenheit ( F = (C × 9/5) + 32 )
Fahrenheit -> Celsius ( C = (F - 32) × \frac{5}{9} )
Celsius -> Kelvin      ( K = C + 273.15 )
Kelvin -> Celsius     ( C = K - 273.15 )
Fahrenheit -> Kelvin  ( K = (F - 32) × \frac{5}{9} + 273.15 )
Kelvin -> Fahrenheit  ( F = (K - 273.15) × \frac{9}{5} + 32 )
 
Eduardo JR Ilagan
"""

from flask import Flask, render_template, request

app = Flask(__name__)

def cnvrt_temp(temp, fromtempto):
    """Temperature Converter"""
    temp=float(temp)
    if fromtempto == "CtoF":
        temp = (temp * (9/5)) + 32
    elif fromtempto == "FtoC":
        temp = ((temp - 32)*5)/9
    elif fromtempto == "CtoK":
        temp = temp + 273.15
    elif fromtempto == "KtoC":
        temp = temp - 273.15
    elif fromtempto == "FtoK":
        temp = (((temp - 32)*5)/9) + 273.15
    elif fromtempto == "KtoF":
        temp = ((temp - 273.15) * 9/5) + 32
    return temp

def temp_input():
    """User Interface CLI"""
    while True:
        print("Choose which Conversion to do")
        print ("1. Celsius -> Fahrenheit")
        print ("2. Fahrenheit -> Celsius")
        print ("3. Celsius -> Kelvin")
        print ("4. Kelvin -> Celsius")
        print ("5. Fahrenheit -> Kelvin")
        print ("6. Kelvin -> Fahrenheit")
        ch = input("Enter Number:")
        cnvrsion = ""
        if ch == "1":
            cnvrsion = "CtoF"
            unit = "F"
            break
        elif ch == "2":
            cnvrsion = "FtoC"
            unit = "C"
            break
        elif ch == "3":
            cnvrsion = "CtoK"
            unit = "K"
            break
        elif ch == "4":
            cnvrsion = "KtoC"
            unit = "C"
            break
        elif ch == "5":
            cnvrsion = "FtoK"
            unit = "K"
            break
        elif ch == "6":
            cnvrsion = "KtoF"
            unit = "F"
            break
    temp = input("Enter Temperature:")
    temp = cnvrt_temp(temp, cnvrsion)
    print(f'{temp} {unit}')

@app.route("/", methods=["GET","POST"])
def web_temp():
    """Flask test - Hello"""
    result = None
    unit = ""
    if request.method == "POST":
        temp = request.form["temp"]
        conversion = request.form["conversion"]
        result = cnvrt_temp(temp, conversion)

        unit = (
            "F" if conversion in ("CtoF", "KtoF") else
            "C" if conversion in ("FtoC", "KtoC") else
            "K"
        )
    return render_template("temp_index.html", result=result, unit=unit)

@app.route('/image')
def show_image():
    """Flask test - Number"""
    return render_template("sample.html")


if __name__ == '__main__':
    app.run (debug=True)
    #temp_input()
