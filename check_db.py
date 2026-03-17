import sqlite3
print("Conectando a DB...")
conn = sqlite3.connect('instance/guardias.db')
print("DB conectada")
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM guardias')
count = cursor.fetchone()[0]
print(f'Guardias en DB: {count}')
conn.close()
print("Done")
