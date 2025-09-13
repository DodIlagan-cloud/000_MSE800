import sqlite3
import time 

def create_connection():
    conn = sqlite3.connect("app.db")
    return conn

class UserService:
    def get_user(self, user_id,conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id, ))
        result = cursor. fetchone ()
        return result

# New connection

class OrderService:
    def get_orders(self, user_id,conn):
        create_connection() # Another new connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
        result = cursor. fetchall()


def create_tables():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    """Creates the table for user"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            user_addr TEXT NOT NULL
        )    ''')
    ('''
        CREATE TABLE IF NOT EXISTS orders (
            ord_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ord_name TEXT NOT NULL,
            ord_stat TEXT NOT NULL
        )    ''')

    conn.commit()
    conn.close()

def insrec(tbl_nme,stu_dtl):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    tbl_col = ", ".join(stu_dtl.keys())
    plchldrs = ", ".join(['?'] * len(stu_dtl))
    col_val = tuple(stu_dtl.values())
    tbl_nme = tbl_nme
    ins_query = f"INSERT INTO {tbl_nme} ({tbl_col}) VALUES ({plchldrs}))"
    print(ins_query)
    print(col_val)
    try:
        cursor.execute(ins_query, tuple(col_val))
        afct_rows = cursor.rowcount
        conn.commit()
        return afct_rows
    except sqlite3.Error as e: 
        print(f"An error occurred during adding record: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()

def add_user():
    stu_name = "Harry Potter"
    stu_addr = "Privet Drive"
    stu_dtl = {'user_name':stu_name,'user_addr':stu_addr}
    tbl_nme = 'users'
    afct_rows = insrec(tbl_nme,stu_dtl)
    if afct_rows:
        print(f"User '{stu_name}' added successfully.")
    else:
        print(f"Failed to add User '{stu_name}'.")


def add_order():
    stu_name = "Wand Order"
    stu_addr = "Y"
    stu_dtl = {'ord_name':stu_name,'ord_stat':stu_addr}
    tbl_nme = 'users'
    afct_rows = insrec(tbl_nme,stu_dtl)
    if afct_rows:
        print(f"Order '{stu_name}' added successfully.")
    else:
        print(f"Failed to add UsOrderer '{stu_name}'.")

def main():
    start = time.perf_counter_ns()
    #create_tables()
    #add_user()
    #add_order()
    conn=create_connection()
    u = UserService()
    #print(u)
    o = OrderService()
    #print(o)
    end = time.perf_counter_ns()
    conn.close()
    print(end-start)

if __name__ == "__main__":
    main()
