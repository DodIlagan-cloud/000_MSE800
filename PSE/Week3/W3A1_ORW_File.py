"""Week 3 - Activity 1 : Open Read Write on the file
Using the attached text file, open, read, and write the complete information for the demo.txt. 
Share the GitHub link here(with adding the screenshot of the result).
W3A1_ORW_File.py - Week 3 Activity 1
Eduardo JR Ilagan
"""


class TextProcess():
    def __init__(self,fileforproc,newfile):
        self.fileforproc = fileforproc
        self.newfile = newfile
    def openfile(self,fileforproc):
        content = open(fileforproc,"r",encoding="UTF-8")
        return content
    def readfile(self, content):
        for line in content:
            print(line[0:-1])
        content.close()
    def writefile(self,newfile):
        with open(newfile,"w",encoding="UTF-8") as writenew:
            writenew.write("This is a new file written\n")
    
    def appendfile(self,newfile):
        with open(newfile,"a",encoding="UTF-8") as appendnew:
            appendnew.write("And this was appended to it.\n")  
                        
def main():
    fileforproc=r"G:\My Drive\00_Pers\000_MSE800\PSE\Week3\demo.txt"
    newfile=r"G:\My Drive\00_Pers\000_MSE800\PSE\Week3\demo_01.txt"
    txt_proc = TextProcess(fileforproc,newfile)
    #content = open(fileforproc,"r",)
    #for line in content:
    #    print(line[0:-1])
    #content.close()
    #print(fileforproc)
    content = txt_proc.openfile(fileforproc)
    txt_proc.readfile(content)
    txt_proc.writefile(newfile)
    txt_proc.appendfile(newfile)
if __name__ == "__main__":
    main()