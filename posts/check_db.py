import sqlite3

conn = sqlite3.connect('blog.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(posts)')
posts_info = cursor.fetchall()
print("Posts table columns:")
for column in posts_info:
    print(column)

cursor.execute('PRAGMA table_info(comments)')
comments_info = cursor.fetchall()
print("Comments table columns:")
for column in comments_info:
    print(column)

conn.close()
