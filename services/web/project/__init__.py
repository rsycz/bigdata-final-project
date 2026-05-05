import os
import psycopg2
from flask import Flask, send_from_directory, render_template, request

app = Flask(__name__)
app.config.from_object("project.config.Config")

def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

@app.route("/")
def index():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * 20

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT users.username, tweets.message, tweets.created_at
        FROM tweets
        JOIN users ON tweets.user_id = users.id
        ORDER BY tweets.created_at DESC
        LIMIT 20 OFFSET %s
    """, (offset,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    tweets = [{'username': r[0], 'message': r[1], 'created_at': r[2]} for r in rows]
    return render_template('index.html', tweets=tweets, page=page)

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)
