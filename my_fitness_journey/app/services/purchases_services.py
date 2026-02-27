# app/services/purchase_service.py

from app.database.database import db
from app.models.purchases import Purchase
from app.models.users import User
from app.models.listings import Listing
from app.models.addresses import Address
from app.models.credits import CreditTxn
from app.services.buyer_protection_config_services import BuyerProtectionService
from app.services.errors import ApiError, NotFoundError, ForbiddenError, ConflictError, UnauthorizedError
import json
from sqlalchemy.exc import IntegrityError # Pour gérer les erreurs de transaction

ADMIN_EMAIL="admin@imt.test"

class PurchaseService:

    # -----------------------------------------------------
    # get (GET /api/purchases)
    # -----------------------------------------------------
    @staticmethod
    def get_purchases(actor_email: str, role: str = None):
        user=User.query.filter_by(email=actor_email).first()
        if not user:
            raise UnauthorizedError("Unauthorized: Missing X-User-Email")
        if role is None or role=="buyer":
            purchases=Purchase.query.filter_by(buyer_email=actor_email).all()
        elif role =="seller":
            purchases = Purchase.query.filter_by(seller_email=actor_email).all()
        else:
            raise ApiError("Invalid role. Must be 'buyer' or 'seller'.")
        return [p.to_dict() for p in purchases]
    
    @staticmethod
    def get_purchase_by_id(actor_email: str, purchase_id: int):
        user = User.query.filter_by(email=actor_email).first()
        if not user:
            raise UnauthorizedError("Unauthorized: Missing X-User-Email")
        purchase=Purchase.query.filter_by(id=purchase_id).first()
        if not purchase:
            raise NotFoundError("Not found")
        if not (actor_email== purchase.buyer_email or actor_email==purchase.seller_email or actor_email==ADMIN_EMAIL):
            raise ForbiddenError("Forbidden: not owner")
        return purchase.to_dict()
        


    # -----------------------------------------------------
    # CREATE (POST /api/purchases)
    # -----------------------------------------------------
    @staticmethod
    def create_purchase(data: dict, buyer_email: str):
        listing_id = data.get("listing_id")
        address_id = data.get("address_id")

        # 1. Vérification de l'existence des ressources
        listing = Listing.query.get(listing_id)
        buyer = User.query.filter_by(email=buyer_email).first()
        address = Address.query.filter_by(id=address_id, user_email=buyer_email).first()
        
        if not (listing and buyer and address):
            raise NotFoundError("Listing, buyer, or address not found.")
            
        # 2. Préconditions : Annonce Active et non vendu à soi-même
        if listing.status != 'active':
            raise ApiError("Bad request: listing not active")
        if listing.seller_email == buyer_email:
            raise ForbiddenError("Forbidden: Cannot purchase your own listing.")

        # 3. Calculs et Snapshot des Prix
        config = BuyerProtectionService.get_config()
        totals = BuyerProtectionService.calculate_totals(
            price_cents=listing.price_cents,
            shipping_cents=listing.shipping_cents,
            config_data=config
        )
        total_cents = totals['total_cents']

        # 4. Vérification des Crédits de l'Acheteur
        if buyer.credits_cents < total_cents:
            raise ApiError("Bad request: insufficient credits")

        try:
            # 5. Début de la Transaction BD (Atomique)
            
            # 5.1 Débit de l'Acheteur (Buyer Debit)
            new_buyer_balance = buyer.credits_cents - total_cents
            buyer.credits_cents = new_buyer_balance
            db.session.add(buyer)

            # 5.2 Création de l'objet Purchase
            purchase = Purchase(
                listing_id=listing_id,
                buyer_email=buyer_email,
                seller_email=listing.seller_email,
                item_price_cents=listing.price_cents,
                shipping_cents=listing.shipping_cents,
                insurance_part_cents=totals['insurance_part_cents'],
                total_cents=total_cents,
                address_snapshot=json.dumps(address.to_dict()), # Stockage du snapshot
                status='paid'
            )
            db.session.add(purchase)
            db.session.flush() # Assure que purchase.id est généré

            # 5.3 Enregistrement des Transactions de Crédit (Ledger)
            
            # Débit Acheteur (type: purchase, montant négatif)
            buyer_txn = CreditTxn(
                user_email=buyer_email,
                type='purchase',
                amount_cents=-total_cents,
                balance_after_cents=new_buyer_balance,
                related_purchase_id=purchase.id
            )
            db.session.add(buyer_txn)

            # Crédit Vendeur (type: sale_payout, montant sans assurance)
            seller_payout = listing.price_cents + listing.shipping_cents
            seller = User.query.filter_by(email=listing.seller_email).first()
            new_seller_balance = seller.credits_cents + seller_payout
            seller.credits_cents = new_seller_balance
            db.session.add(seller)

            seller_txn = CreditTxn(
                user_email=listing.seller_email,
                type='sale_payout',
                amount_cents=seller_payout,
                balance_after_cents=new_seller_balance,
                related_purchase_id=purchase.id
            )
            db.session.add(seller_txn)
            
            # 5.4 Mise à jour du Statut de l'Annonce (Listing)
            listing.status = 'sold'
            db.session.add(listing)

            # 6. Commit final de la transaction atomique
            db.session.commit()
            return purchase.to_dict()

        except IntegrityError:
            db.session.rollback()
            raise ApiError("Transaction failed due to integrity constraint.")
    
    # -----------------------------------------------------
    # DECLARE OUTCOME (POST /api/purchases/{id}/declare)
    # -----------------------------------------------------
    @staticmethod
    def declare_outcome(purchase_id: int, data: dict, actor_email: str):
        purchase = Purchase.query.get(purchase_id)
        
        if not purchase:
            raise NotFoundError("Purchase not found")
            
        # 1. Vérification des droits (Seul l'acheteur peut déclarer)
        if purchase.buyer_email != actor_email:
            raise ForbiddenError("Forbidden: Only the buyer can declare an outcome.")

        # 2. Vérification de l'état (Idempotence)
        # Si c'est déjà fini, on ne peut pas changer l'issue
        if purchase.status in ['closed', 'refunded']:
            raise ConflictError("Conflict: Purchase is already terminal (closed or refunded).")

        # 3. Validation de l'entrée
        outcome = data.get("status")
        valid_outcomes = ["OK", "NOT_RECEIVED", "NOT_AS_DESCRIBED"]
        if outcome not in valid_outcomes:
            raise ApiError(f"Invalid status. Must be one of {valid_outcomes}")

        # 4. Traitement selon l'issue
        if outcome == "OK":
            # Tout s'est bien passé, on ferme le dossier
            purchase.status = "closed"
            
        else:
            # Cas de Litige : NOT_RECEIVED ou NOT_AS_DESCRIBED
            # -> Remboursement à l'acheteur
            purchase.status = "refunded"
            
            # Calcul du montant à rembourser (Prix objet + Port, mais PAS l'assurance)
            refund_amount = purchase.item_price_cents + purchase.shipping_cents
            
            # Crédit du compte acheteur
            buyer = User.query.filter_by(email=actor_email).first()
            buyer.credits_cents += refund_amount
            db.session.add(buyer)
            
            # Enregistrement de la transaction (Ledger)
            txn = CreditTxn(
                user_email=actor_email,
                type='refund',
                amount_cents=refund_amount,
                balance_after_cents=buyer.credits_cents,
                related_purchase_id=purchase.id
            )
            db.session.add(txn)

        # 5. Commit des changements
        db.session.commit()
        
        # On retourne l'objet mis à jour (ou juste un message, selon préférence)
        return purchase.to_dict()