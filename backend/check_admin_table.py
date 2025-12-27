import sqlite3

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admins'")
table = cursor.fetchone()
if table:
    print("Table 'admins' exists.")
    cursor.execute("PRAGMA table_info(admins)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
else:
    print("Table 'admins' does not exist.")
conn.close()
