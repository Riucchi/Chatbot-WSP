import sqlite3

conn = sqlite3.connect('whatsapp_bot.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tablas en la base de datos:", tables)
conn.close()