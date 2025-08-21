"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSDatabase.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""

import sqlite3

def create_connection():
    conn = sqlite3.connect("YSDDB.db")
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    """Creates the table for Students"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            stu_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stu_name TEXT NOT NULL,
            stu_addr TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            tran_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stu_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            pd_date TEXT NOT NULL,
            FOREIGN KEY (stu_id) references students (stu_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructors (
            inst_id INTEGER PRIMARY KEY AUTOINCREMENT,
            inst_name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            crse_id INTEGER PRIMARY KEY AUTOINCREMENT,
            crse_name TEXT NOT NULL,
            crse_timeframe TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            sbjt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sbjt_name TEXT NOT NULL,
            sbjt_sched TEXT NOT NULL,
            crse_id INTEGER NOT NULL,
            inst_id INTEGER NOT NULL,
            FOREIGN KEY (crse_id) references course (crse_id),
            FOREIGN KEY (inst_id) references course (inst_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS class_records (
            sbjt_id INTEGER NOT NULL,
            stu_id INTEGER NOT NULL,
            inst_id INTEGER NOT NULL,
            marking TEXT,
            PRIMARY KEY (stu_id,sbjt_id,inst_id) 
            FOREIGN KEY (stu_id) references student (stu_id),
            FOREIGN KEY (inst_id) references instsructor (inst_id),
            FOREIGN KEY (sbjt_id) references subject (sbjt_id)
        )
    ''')
    conn.commit()
    conn.close()