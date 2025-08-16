"""Week 3 - Activity 2 : Count the words in the file
Using the attached text file, open, read, and write the complete information for the demo.txt. 
Share the GitHub link here(with adding the screenshot of the result).
W3A2_ORW_File.py - Week 3 Activity 1
Eduardo JR Ilagan
"""


class TextProcess():
    def __init__(self,fileforproc):
        self.fileforproc = fileforproc
    def openfile(self,fileforproc):
        with open(fileforproc,"r",encoding="UTF-8") as data:
            content = data.read()
            print(content)
            return content
    def countwords(self,data):
        return data.split()
    def get_words(self,text):
        return self.text.split()

def main():
    fileforproc=r"G:\My Drive\00_Pers\000_MSE800\PSE\Week3\demo.txt"
    txt_proc = TextProcess(fileforproc)
    content = txt_proc.openfile(fileforproc)
    words = txt_proc.countwords(content)
    print("number of words",len(words))
    

if __name__ == "__main__":
    main()