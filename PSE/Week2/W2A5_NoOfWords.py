class StringManipulator:
    def __init__(self,text):
        self.text = text
    def find_character(self,char,text):
        self.text = text
        return self.text.find(char)
    
    def find_legnth(self,text):
        return len(self.text)
    
    def convert_capsup(self,text):
        return self.text.upper()
    
    def get_words(self,text):
        return self.text.split()

def main():
    name = StringManipulator(text=input("enter a sentence:".strip().lower()))
    result = name.get_words(name)
    print("number of words",len(result))

if __name__ == "__main__":
    main()
