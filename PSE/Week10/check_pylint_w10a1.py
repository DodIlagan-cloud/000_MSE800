""" 
Develop an Object-Oriented (OO) Python project that reads either a string or a list, 
then 
performs two analyses:
Calculates the total length.
Determines the number of uppercase characters.
The project should be structured with appropriate classes and methods.pylint W10A1.py 
After implementation, use Pylint to analyze and improve the code quality, 
ensuring adherence to Python’s best practices and style guidelines. 
Share the result when you have done
 """

def get_str():
    """function to get string"""
    strvar = input(" Please enter a text:" )
    return strvar

def str_len(strvar):
    """function to check for legnth"""
    strlen = len(strvar)
    return strlen

def str_cap(strvar):
    """function to get caps letters"""
    capcnt = 0
    for ch in strvar:
        if ch.isupper():
            capcnt = capcnt + 1
    return capcnt

def main():
    """ main funcnction """
    strvar = get_str()
    strlen = str_len(strvar)
    capcnt = str_cap(strvar)
    print(strlen,capcnt)

if __name__ == "__main__" :
    main()
