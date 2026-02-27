from app.database.database import db
from sqlalchemy import CheckConstraint, Enum, Text
from datetime import datetime

class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    
    # 1. Liens et Rôles
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    buyer_email = db.Column(db.String(100), db.ForeignKey('user.email'), nullable=False)
    seller_email = db.Column(db.String(100), nullable=False) # Ne pas mettre de FK pour ne pas être impacté par la suppression admin
    
    # 2. Snapshot des Prix (Crucial pour le Tier A)
    item_price_cents = db.Column(db.Integer, nullable=False)
    shipping_cents = db.Column(db.Integer, nullable=False)
    insurance_part_cents = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    
    # 3. Snapshot de l'Adresse
    # L'adresse est stockée en texte/JSON (snapshot) pour que l'historique de l'achat 
    # ne change pas si l'utilisateur modifie son adresse plus tard.
    # On stocke ici la représentation JSON de l'adresse (line1, city, postal_code, etc.)
    address_snapshot = db.Column(Text, nullable=False) 
    
    # 4. Statut
    status = db.Column(
        Enum("paid", "delivered", "closed", "refunded", name="purchase_status_enum", create_type=True),
        default="paid",
        nullable=False
    )
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation inverse pour lier les transactions de crédits à cet achat
    txns = db.relationship("CreditTxn", backref="purchase", lazy=True) #accéder à toutes les transactions liées à cet achat via purchase.txns.
    
    def to_dict(self):
        # Nécessite une conversion du champ address_snapshot (Text) vers un objet Address (dict)
        import json
        address_dict = json.loads(self.address_snapshot) 
        
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "buyer_email": self.buyer_email,
            "seller_email": self.seller_email,
            "item_price_cents": self.item_price_cents,
            "shipping_cents": self.shipping_cents,
            "insurance_part_cents": self.insurance_part_cents,
            "total_cents": self.total_cents,
            "address": address_dict, # L'adresse sous forme d'objet/dict
            "status": self.status,
            "created_at": self.created_at.isoformat().replace('+00:00', 'Z')
        }