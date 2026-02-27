from app.database.database import db
from app.models.credits import CreditTxn
from app.models.users import User
from app.services.errors import ApiError, NotFoundError

class CreditService:
    
    # -----------------------------------------------------
    # Top-up - POST /api/credits/topup
    # -----------------------------------------------------
    @staticmethod
    def topup_credits(actor_email: str, amount_cents: int):
        if amount_cents <= 0:
            raise ApiError("Amount must be greater than 0 cents.")

        user = User.query.filter_by(email=actor_email).first()
        if not user:
            raise NotFoundError("User account not found.")

        # 1. Mise à jour du solde utilisateur
        new_balance = user.credits_cents + amount_cents
        user.credits_cents = new_balance
        db.session.add(user)

        # 2. Création de l'enregistrement de transaction (ledger)
        txn = CreditTxn(
            user_email=actor_email,
            type='topup',
            amount_cents=amount_cents,
            balance_after_cents=new_balance,
            related_purchase_id=None
        )
        db.session.add(txn)
        db.session.commit()
        
        return {"balance_cents": new_balance}
        
    # -----------------------------------------------------
    # Relevé de Compte - GET /api/credits/ledger
    # -----------------------------------------------------
    @staticmethod
    def get_ledger(actor_email: str):
        user = User.query.filter_by(email=actor_email).first()
        if not user:
            raise NotFoundError("User account not found.")
            
        # Récupère toutes les transactions, triées de la plus récente à la plus ancienne
        txns = CreditTxn.query.filter_by(user_email=actor_email).order_by(CreditTxn.created_at.desc()).all()
        
        return {
            "balance_cents": user.credits_cents,
            "txns": [t.to_dict() for t in txns]
        }