
from app.database.database import db
from sqlalchemy import CheckConstraint

class Address(db.Model):
    __tablename__ = "addresses"
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), db.ForeignKey("user.email"), nullable=False) # L'utilisateur propriétaire
    
    line1 = db.Column(db.String(200), nullable=False)
    line2 = db.Column(db.String(200), nullable=True)  # Peut être null (Tier A)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "line1": self.line1,
            "line2": self.line2, # Retourne null si la colonne est NULL
            "city": self.city,
            "postal_code": self.postal_code
        }