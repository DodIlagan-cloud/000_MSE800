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
    def __init__ (self, stu_name,stu_addr,stu_age,stu_id,sbjt_id):
        super().__init__(stu_name, stu_addr, stu_age)
        self.stu_id = stu_id
        self.sbjt_id = sbjt_id
        
    def insrec(self,tbl_nme,stu_dtl):
        tbl_col = ", ".join(stu_dtl.keys())
        plchldrs = ", ".join(['?'] * len(stu_dtl))
        col_val = tuple(stu_dtl.values())
        tbl_nme = tbl_nme
        ins_query = f"INSERT INTO {tbl_nme} ({tbl_col}) VALUES ({plchldrs}))"
        print(f"This is the insert query: cursor.execute({ins_query} , {col_val})")

def add_student():
    stu_name = input("Name: ")
    stu_addr = input("Addres: ")
    stu_age = input("Age: ")
    os = student(stu_name,stu_addr,stu_age,12347,2) 
    stu_dtl = {'stu_name':stu_name,'stu_addr':stu_addr, 'stu_age' :stu_age,'sbjt_id':os.sbjt_id,'stu_id': os.stu_id}
    tbl_nme = 'students'
    #afct_rows = 
    os.insrec(tbl_nme,stu_dtl)
    #if afct_rows:
    #    print(f"Student '{stu_name}' added successfully.")
    #else:
    #    print(f"Failed to add student '{stu_name}'.")
    #print(user1.user_detail())
    

def main():
    user1 = User("Harry Potter","Privet Drive", 11)
    add_student()


if __name__ == "__main__":
    main()