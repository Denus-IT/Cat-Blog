import sqlite3

conn = sqlite3.connect('blog.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE posts ADD COLUMN likes INTEGER DEFAULT 0')
    print("Column 'likes' added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
