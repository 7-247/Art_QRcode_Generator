import sqlite3
con = sqlite3.connect("Class.db",check_same_thread=False)
cursor = con.cursor()
cursor.execute("select * from USED")
result = cursor.fetchall()
for i in result:
	print(i)
cursor.close()
con.close()
