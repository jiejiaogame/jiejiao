import sqlite3
conn = sqlite3.connect("honghuang.db")
c = conn.cursor()
c.execute("UPDATE users SET occupied_by = NULL WHERE occupied_by = ''")
conn.commit()
conn.close()