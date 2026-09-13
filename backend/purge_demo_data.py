import sqlite3
import os

db_path = 'safemetric.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Delete ALL inspections and related data (demo seeder + test runs)
c.execute("DELETE FROM inspection_fields")
c.execute("DELETE FROM reports")
c.execute("DELETE FROM inspections")

# Keep only real registered users: ID=1 (officer@safemetric.gov.in), ID=2 (mani@gmail.com), ID=16 (mani2006@gmail.com)
c.execute("DELETE FROM users WHERE id NOT IN (1, 2, 16)")

conn.commit()

# Verify
c.execute('SELECT COUNT(*) FROM inspections')
print('Inspections remaining:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM users')
print('Users remaining:', c.fetchone()[0])
c.execute('SELECT id, name, email, role FROM users')
print('Remaining users:')
for row in c.fetchall():
    print(f'  ID={row[0]}, name={row[1]}, email={row[2]}, role={row[3]}')
conn.close()
print('Database cleaned successfully!')
