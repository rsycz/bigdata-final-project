import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/project/static"
