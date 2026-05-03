import os
import psycopg2
from flask import Flask, send_from_directory

app = Flask(__name__)
app.config.from_object("project.config.Config")

def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

@app.route("/")
def hello_world():
    return "Twitter clone coming soon!"

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)
