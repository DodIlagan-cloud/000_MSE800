class StringManipulator:
    def __init__(self,text):
        self.text = text
    def find_character(self,char):
        #self.text = text
        return self.text.find(char)
    
    def find_legnth(self,text):
        return len(self.text)
    
    def convert_capsup(self,text):
        return self.text.upper()

def main():
    name = StringManipulator(text=input("enter a word:".strip().lower()))
    result = name.find_character(input("enter character:").strip().lower())
    print("index of Char",result)
    result_length = name.find_legnth(name)
    print ("size of word:",result_length)
    result_up = name.convert_capsup(name)
    print ("all caps:",result_up)

if __name__ == "__main__":
    main()
