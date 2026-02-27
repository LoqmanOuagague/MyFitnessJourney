from app.database.database import db
from sqlalchemy import CheckConstraint, ForeignKey, Enum
from datetime import datetime
import enum

# ✅ AJOUT : La classe Enum indispensable pour les imports externes (init_db)
class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    DELETED = "deleted"


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    seller_email = db.Column(db.String(100), db.ForeignKey("user.email"), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.String(5000), nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    shipping_cents = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    
    status = db.Column(
        Enum(ListingStatus),             # <--- LA CORRECTION EST ICI
        default=ListingStatus.ACTIVE,    # On utilise la constante
        nullable=False
    )
    
    photos = db.relationship("Photo", backref="listing", cascade="all, delete-orphan") 
    
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="check_price_positive"),
        CheckConstraint("shipping_cents >= 0", name="check_shipping_positive"),
    )

    def to_dict(self, include_photos=False):
        data = {
            "id": self.id,
            "seller_email": self.seller_email,
            "title": self.title,
            "description": self.description,
            "price_cents": self.price_cents,
            "shipping_cents": self.shipping_cents,
            "category_id": self.category_id,
            # Conversion sécurisée de l'Enum en String
            "status": self.status.value if hasattr(self.status, 'value') else self.status,
            "created_at": self.created_at.isoformat().replace('+00:00', 'Z') if self.created_at else None
        }
        
        # On ajoute les photos seulement si demandé
        if include_photos:
             data["photos"] = [p.to_dict() for p in self.photos]
             
        return data