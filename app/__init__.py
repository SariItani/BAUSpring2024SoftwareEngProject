# app/__init__.py
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin

app = Flask(__name__, template_folder='../templates')
app.config['SECRET_KEY'] = '9d125d217fca3a2938b669e0553189a4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)


login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    imgpath = db.Column(db.String(255))
    bio = db.Column(db.Text)

    def __init__(self, username, email, password, imgpath=None, bio=None):
        self.username = username
        self.email = email
        self.password = password
        self.imgpath = imgpath
        self.bio = bio


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship('User', backref=db.backref('messages', lazy=True))
    message_type = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, content, sender, message_type):
        self.content = content
        self.sender = sender
        self.message_type = message_type


from app import routes
