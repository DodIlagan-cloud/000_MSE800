"""Week 3 - Activity 5: update the sample code "Sample_code_SQLite3"
Please add a new table named "Students" with three columns: Stu_ID, Stu_name, and Stu_address. 
Insert two sample records into Students, then display all rows from both the Users and Students tables.
database.py - Week 3 Activity 5
Eduardo JR Ilagan
"""

import sqlite3

def create_connection():
    conn = sqlite3.connect("users.db")
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Start EJP W3A5
def create_student_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            Stu_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Stu_name TEXT NOT NULL,
            Stu_address TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
# End  EJP W3A5