from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(120),nullable=False)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime,default=datetime.utcnow)


    def __repr__(self):
        return f"<Item {self.id} {self.title}>"
    
    

