from flask import Flask, request, redirect, url_for, render_template
import os
import sqlite3
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

conn = sqlite3.connect('blog.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT,
        likes INTEGER DEFAULT 0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        comment TEXT NOT NULL,
        avatar_url TEXT,
        FOREIGN KEY (post_id) REFERENCES posts(id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        avatar_url TEXT
    )
''')

try:
    cursor.execute('ALTER TABLE comments ADD COLUMN avatar_url TEXT')
except sqlite3.OperationalError:
    pass

conn.commit()

def is_valid_input(title, content, image):
    if not title or not content or not image or image.filename == '':
        return False
    return True

@app.route('/')
def index():
    posts = get_posts()
    return render_template('index.html', posts=posts)

@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')
        
        if not is_valid_input(title, content, image):
            error = "Будь ласка, заповніть всі поля та додайте зображення."
            return render_template('add.html', error=error)
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        image_url = f'/static/uploads/{filename}'
        
        add_post_to_database(title, content, image_url)
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    cursor.execute('SELECT image_url FROM posts WHERE id = ?', (post_id,))
    image_url = cursor.fetchone()[0]

    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    cursor.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    conn.commit()

    if image_url:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_url.lstrip('/'))
        print(f"Шлях до файлу: {image_path}")
        try:
            os.remove(image_path)
            print(f"Зображення {image_path} успішно видалено.")
        except FileNotFoundError:
            print(f"Помилка: Зображення {image_path} не знайдено.")
        except OSError as e:
            print(f"Помилка видалення зображення: {e}")
        except Exception as e:
            print(f"Помилка видалення зображення: {e}")

    return redirect(url_for('index'))

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    comment = request.form['comment']
    avatar = request.files.get('avatar')

    if not comment or not avatar or avatar.filename == '':
        error = "Будь ласка, заповніть всі поля та додайте аватар."
        return redirect(url_for('index', error=error))

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{secure_filename(avatar.filename)}"
    avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    avatar.save(avatar_path)
    avatar_url = f'/static/uploads/{filename}'

    cursor.execute('INSERT INTO comments (post_id, comment, avatar_url) VALUES (?, ?, ?)', (post_id, comment, avatar_url))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    cursor.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
    conn.commit()
    return redirect(url_for('index'))

def add_post_to_database(title, content, image_url):
    cursor.execute('''
        INSERT INTO posts (title, content, image_url)
        VALUES (?, ?, ?)
    ''', (title, content, image_url))
    conn.commit()

def get_posts():
    cursor.execute('''
        SELECT p.id, p.title, p.content, p.image_url, p.likes, c.id, c.comment, c.avatar_url
        FROM posts p
        LEFT JOIN comments c ON p.id = c.post_id
        ORDER BY p.id DESC, c.id ASC
    ''')
    rows = cursor.fetchall()
    posts = {}
    for row in rows:
        post_id = row[0]
        if post_id not in posts:
            posts[post_id] = {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'image_url': row[3],
                'likes': row[4],
                'comments': []
            }
        if row[5]:
            posts[post_id]['comments'].append({
                'id': row[5],
                'comment': row[6],
                'avatar_url': row[7]
            })
    return list(posts.values())

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = get_post_by_id(post_id)
    if post is None:
        return "Post not found", 404
    return render_template('view_post.html', post=post)

def get_post_by_id(post_id):
    cursor.execute('SELECT title, content, image_url FROM posts WHERE id = ?', (post_id,))
    row = cursor.fetchone()
    if row:
        return {'title': row[0], 'content': row[1], 'image_url': row[2]}
    return None

if __name__ == '__main__':
    app.run(debug=True)