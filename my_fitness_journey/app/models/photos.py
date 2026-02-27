# app/models/photos.py

from app.database.database import db
from sqlalchemy import CheckConstraint, ForeignKey

class Photo(db.Model):
    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
   
    extension = db.Column(db.String(10), nullable=False)
    
    is_thumbnail = db.Column(db.Boolean, default=False, nullable=False)
    
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=True) 

    __table_args__ = (
        CheckConstraint("length(url) > 0", name="check_url_nonempty"),
    )

    def to_dict(self):
        return {
            "url": self.url,
            "is_thumbnail": self.is_thumbnail
        }