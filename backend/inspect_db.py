import sqlite3
import os

db_path = 'safemetric.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print('Tables:', tables)

for t in tables:
    c.execute(f'SELECT COUNT(*) FROM {t}')
    count = c.fetchone()[0]
    print(f'  {t}: {count} records')

# Show inspection data
if 'inspections' in tables:
    c.execute("SELECT id, product_name, compliance_status, image_path, created_at FROM inspections ORDER BY created_at")
    print('\nInspections:')
    for row in c.fetchall():
        print(f'  ID={row[0]}, name={row[1]}, status={row[2]}, img={row[3]}, created={row[4]}')

# Show user data
if 'users' in tables:
    c.execute("SELECT id, name, email, role FROM users")
    print('\nUsers:')
    for row in c.fetchall():
        print(f'  ID={row[0]}, name={row[1]}, email={row[2]}, role={row[3]}')

conn.close()
