from app.database.database import db
from sqlalchemy import CheckConstraint, Enum
from datetime import datetime

class CreditTxn(db.Model):
    __tablename__ = 'credit_txns'

    id = db.Column(db.Integer, primary_key=True)
    
    # Lien vers l'utilisateur concerné par la transaction
    user_email = db.Column(db.String(100), db.ForeignKey("user.email"), nullable=False)
    
    # Type de transaction (imposé par le Tier A)
    type = db.Column(
        Enum("topup", "purchase", "refund", "sale_payout", name="txn_type_enum", create_type=True),
        nullable=False
    )
    
    # Montant du mouvement (positif pour crédit, négatif pour débit)
    amount_cents = db.Column(db.Integer, nullable=False)
    
    # Solde après cette transaction (toujours >= 0)
    balance_after_cents = db.Column(db.Integer, nullable=False)
    
    # Référence optionnelle à l'achat (pour les types purchase, refund, sale_payout)
    related_purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=True) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        # CheckConstraint('balance_after_cents >= 0', name='check_balance_non_negative'), # Généralement géré par la logique
    )

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "amount_cents": self.amount_cents,
            "balance_after_cents": self.balance_after_cents,
            "related_purchase_id": self.related_purchase_id,
            "created_at": self.created_at.isoformat().replace('+00:00', 'Z')
        }