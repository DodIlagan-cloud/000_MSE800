
    
#from YSDatabase import drop_tab,check_tables
from YSstu_manager import add_student,view_student,delete_student,check_stu_pay
from YSvalidations import chk_int,date_valid
from datetime import datetime
import sqlite3

def create_connection():
    conn = sqlite3.connect("YSDDB.db")
    return conn
""""Functions for troubleshooting while building the system"""
def drop_tab():
    conn = create_connection()
    cursor = conn.cursor()
    """Drops the table for Students"""
    #cursor.execute('''DROP TABLE IF EXISTS students''')
    #cursor.execute('''DROP TABLE IF EXISTS payments''')
    cursor.execute('''DROP TABLE IF EXISTS instructor''')
    cursor.execute('''DROP TABLE IF EXISTS subject''')
    cursor.execute('''DROP TABLE IF EXISTS course''')
    cursor.execute('''DROP TABLE IF EXISTS class_record''')
    conn.commit()
    conn.close()

def check_tables():

    conn = create_connection()
    cursor = conn.cursor()
    rows = cursor.execute(f"SELECT * FROM instructors ")
    print(cursor.fetchall())
    column_aliases = [description[0] for description in cursor.description]
    cursor.execute(f"SELECT * FROM subjects")
    print(cursor.fetchall())
    column_aliases = [description[0] for description in cursor.description]
    cursor.execute(f"SELECT * FROM class_records")
    print(cursor.fetchall())
    column_aliases = [description[0] for description in cursor.description]
#from datetime import datetime
# ... (database connection setup) ...
# cursor.execute("INSERT INTO my_events (event_name, event_date) VALUES (?, ?)", ('Meeting', datetime.now().strftime('%Y-%m-%d')))

    

    #rows1 = cursor.execute("SELECT * FROM payments WHERE stu_id = ? AND pd_date = ?",(stu_id,pd_date))
    #print(cursor.fetchall())
    conn.commit()
    conn.close()

def check_query(clsrec_stuid):
    conn = create_connection()
    cursor = conn.cursor()
    search_pattern = f"{clsrec_stuid}"
    search_query = f"""SELECT st.stu_name Student,
                                cl.stu_id clstuid,
                                cl.inst_id clinstid,
                                cl.sbjt_id clsbjtid,
                                s.sbjt_name Subject
                           FROM class_records cl,
                                students st,
                                subjects s
                          WHERE cl.stu_id = st.stu_id
                            AND cl.sbjt_id = s.sbjt_id
                    """
    cursor.execute(search_query)
    #,(search_pattern,)
    #      AND cl.stu_id = ?                      
    # Get Column Names (Aliases) from cursor.description
    rows = cursor.fetchall()
    if rows :
        print("Record found from record.")
    else:
        print(f"No record for Student ID'{clsrec_stuid}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

def main():
    #drop_tab()
    check_tables()
    #check_stu_pay(1)
    clsrec_stuid = "4"
    search=check_query(clsrec_stuid)

    for search in search:
        print(search)
    #pd_date = input("Enter date amount was paid (YYYY-MM-DD): ")
    #pd_date_chk = date_check(pd_date)
    #while pd_date_chk == False: 
    #    print(pd_date_chk)
    #    pd_date = input("Incorrect Date format Entered: Please enter date with format this YYYY-MM-DD: ")
    #    pd_date_chk = date_check(pd_date)
    #    if pd_date_chk == True:
    #        break
    #print(pd_date)

        #int_val_chk = int_check(int_val)
    #check = is_int_check = isinstance(int_val, int) 
    #print (check)
    #int_val = input("Enter amount paid in NZD: ")
    #amount = chk_int(int_val)
    #print(amount)



def get_validated_integer_input(prompt_message: str) -> int:
    """
    Prompts the user for input until a valid integer is entered.
    Returns the validated integer.
    """
    while True: # Loop indefinitely until a valid integer is returned
        user_input = input(prompt_message)
        try:
            # Attempt to convert the user's input to an integer
            integer_value = int(user_input)
            # If successful, break out of the loop and return the value
            return integer_value
        except ValueError:
            # If a ValueError occurs (e.g., input is not a whole number or empty),
            # print an error message and the loop will continue to the next iteration,
            # prompting the user again.
            print("Invalid input. Please enter a whole number.")

def date_check(pd_date):
    try:
        is_date = datetime.strptime(pd_date, "%Y-%m-%d")
        return True
        #print(is_date)
    except ValueError:
        return False
    #if is_date:
if __name__ == "__main__":
    main()