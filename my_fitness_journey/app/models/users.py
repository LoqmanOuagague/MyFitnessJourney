from app.database.database import db
from sqlalchemy import CheckConstraint


class User(db.Model):
    email = db.Column(db.String(100), primary_key=True)
    credits_cents = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    __table_args__ = (
        CheckConstraint('credits_cents >= 0', name='check_credit_positive'),
    )

    def to_dict(self):
        return {
            "email": self.email,
            "name": self.name,
            "credits_cents": self.credits_cents,
        }
