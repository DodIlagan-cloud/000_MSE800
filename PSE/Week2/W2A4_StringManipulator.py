class StringManipulator:
    #def __init__(self,text): -- Init used to inialize the variables that the class will be using.
    #    self.text = text
    def find_character(self,char,text):
        self.text = text
        return self.text.find(char)
    
    def find_legnth(self,text):
        return len(self.text)
    
    def convert_capsup(self,text):
        return self.text.upper()

def main():
    name = StringManipulator() # since init is gone, the class doesnt take any argumentss
    text=input("enter a word:".strip().lower()) # the text variable that the class will be using is declared as global variable here.
    result = name.find_character(input("enter character:").strip().lower(),text)
    print("index of Char",result)
    result_length = name.find_legnth(name)
    print (result_length)
    result_up = name.convert_capsup(name)
    print (result_up)

if __name__ == "__main__":
    main()
