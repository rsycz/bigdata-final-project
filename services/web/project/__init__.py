import os
import psycopg2
from flask import Flask, send_from_directory, render_template, request, session, redirect, url_for, flash
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config.from_object("project.config.Config")
bcrypt = Bcrypt(app)

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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT credentials.password_hash
            FROM users
            JOIN credentials ON users.id = credentials.user_id
            WHERE users.username = %s
        """, (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None or not bcrypt.check_password_hash(row[0], password):
            flash("Invalid username or password", "error")
            return render_template("login.html")

        session["username"] = username
        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("create_account.html")

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username)
                VALUES (%s)
                RETURNING id
            """, (username,))
            user_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO credentials (user_id, password_hash)
                VALUES (%s, %s)
            """, (user_id, password_hash))
            conn.commit()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("Username already exists", "error")
            return render_template("create_account.html")
        finally:
            cur.close()
            conn.close()

    return render_template("create_account.html")

@app.route("/create_message", methods=["GET", "POST"])
def create_message():
    if "username" not in session:
        flash("You must be logged in to post a message", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        message = request.form["message"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (session["username"],))
        user_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO tweets (user_id, message)
            VALUES (%s, %s)
        """, (user_id, message))
        conn.commit()
        cur.close()
        conn.close()

        flash("Tweet posted!", "success")
        return redirect(url_for("index"))

    return render_template("create_message.html")

@app.route("/search")
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * 20
    tweets = []

    if query:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                users.username,
                ts_headline('english', tweets.message, plainto_tsquery('english', %s),
                    'StartSel=<mark>, StopSel=</mark>') AS message,
                tweets.created_at
            FROM tweets
            JOIN users ON tweets.user_id = users.id
            WHERE to_tsvector('english', tweets.message) @@ plainto_tsquery('english', %s)
            ORDER BY ts_rank(to_tsvector('english', tweets.message), plainto_tsquery('english', %s)) DESC
            LIMIT 20 OFFSET %s
        """, (query, query, query, offset))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        tweets = [{'username': r[0], 'message': r[1], 'created_at': r[2]} for r in rows]

    return render_template('search.html', tweets=tweets, query=query, page=page)

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)
