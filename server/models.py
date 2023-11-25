from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from datetime import datetime

db = SQLAlchemy()



@dataclass
class Users(db.Model):
    __tablename__ = "users"

    id: int = db.Column(db.BigInteger, primary_key=True)
    email: str = db.Column(db.String, nullable=False)
    password: str = db.Column(db.String, nullable=False)



@dataclass
class Robots(db.Model):
    __tablename__ = "robots"

    id: int = db.Column(db.BigInteger, primary_key=True)
    robot_name: str = db.Column(db.String, nullable=False)
    description: str = db.Column(db.String, nullable=False)




@dataclass
class ChatHistory(db.Model):
    __tablename__ = "chathistory"

    id: int = db.Column(db.BigInteger, primary_key=True)
    message: str = db.Column(db.String(10000), nullable=False)
    conversation_id: int = db.Column(db.BigInteger, nullable=False)
    user_id: int = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    robot_id: int = db.Column(db.BigInteger, db.ForeignKey("robots.id"))
    is_robot: bool = db.Column(db.Boolean, nullable=False)
    update_time: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Define the relationships with Users and Robots using the db.relationship function
    user = db.relationship("Users", backref="chathistory", lazy=True)
    robot = db.relationship("Robots", backref="chathistory", lazy=True)
