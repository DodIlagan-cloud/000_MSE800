#learning about overriding methods

class User:
    def __init__ (self, name, addr, age):
        self.name = name
        self.addr = addr
        self.age = age

    def user_detail(self):
        return "User({}, {})".format(self.name, self.age)
        
    def greet(self):
        print("Greetings and Take Care!!!" + self.name)

class student(User):
    def __init__ (self, name, addr, age,stu_id,sbjt_id):
        super().__init__(name, addr, age)
        self.stu_id = stu_id
        self.sbjt_id = sbjt_id
        
    def insrec(self,tbl_nme,stu_dtl):
        tbl_col = ", ".join(stu_dtl.keys())
        plchldrs = ", ".join(['?'] * len(stu_dtl))
        col_val = tuple(stu_dtl.values())
        tbl_nme = tbl_nme
        ins_query = f"INSERT INTO {tbl_nme} ({tbl_col}) VALUES ({plchldrs}))"
        print(f"This is the insert query: cursor.execute({ins_query} , {col_val})")

    def add_student(self):
        stu_dtl = {'stu_name':name,'stu_addr':addr, 'stu_age' :age,'sbjt_id':os.sbjt_id,'stu_id': os.stu_id}
        tbl_nme = 'students'
        return tbl_nme,stu_dtl


def main():
    user1 = User("Harry Potter","Privet Drive", 11)
    #stu_name = input("Name: ")
    #stu_addr = input("Addres: ")
    #stu_age = input("Age: ")
    name = "Ron Weasely"
    addr = "The Burrow"
    age = 11
    os = student(name,addr,age,12347,2) 
    ins_detl = os.add_student()
    os.insrec(ins_detl[0],ins_detl[1])

if __name__ == "__main__":
    main()