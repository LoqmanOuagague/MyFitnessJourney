
from app.database.database import db
from sqlalchemy import CheckConstraint

class BuyerProtectionConfig(db.Model):
    __tablename__ = 'buyer_protection_config'
    
    # Un ID constant (ou un PK unique) car il n'y a qu'une seule ligne de config
    id = db.Column(db.Integer, primary_key=True, default=1) 
    
    # Pourcentage de l'assurance (peut être un nombre décimal)
    ratio_percent = db.Column(db.Float, nullable=False)
    
    # Montant fixe (en centimes) de l'assurance (entier)
    bias_cents = db.Column(db.Integer, nullable=False) 
    
    __table_args__ = (
        CheckConstraint('ratio_percent >= 0', name='check_ratio_positive'),
        CheckConstraint('bias_cents >= 0', name='check_bias_positive'),
    )
    
    def to_dict(self):
        return {
            "ratio_percent": self.ratio_percent,
            "bias_cents": self.bias_cents
        }