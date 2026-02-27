

from app.database.database import db
from app.models.buyer_protection_config import BuyerProtectionConfig
from app.services.errors import ConflictError, NotFoundError # Si vous les utilisez


def round_half_up(n):
    if n >= 0:
        return int(n + 0.5)
    else:
        return int(n - 0.5)

class BuyerProtectionService:

    # 1. Lire la configuration (GET /api/config/buyer-protection)
    @staticmethod
    def get_config():
        # Récupère la seule ligne de configuration (avec PK=1)
        config = BuyerProtectionConfig.query.get(1)
        if not config:
            # Si la base est vide (premier lancement), retourne une configuration par défaut ou lève une erreur
            # Pour l'étape, il est conseillé d'insérer une valeur initiale
            # Ex: (5.5, 200) -> 5.5% + 2€
            raise NotFoundError("Configuration not found. Please initialize.")
        return config.to_dict()

    # 2. Mettre à jour la configuration (PUT /api/config/buyer-protection)
    @staticmethod
    def update_config(data: dict):
        config = BuyerProtectionConfig.query.get(1)
        
        if not config:
            # Crée l'objet si la table est vide
            config = BuyerProtectionConfig(id=1, ratio_percent=data['ratio_percent'], bias_cents=data['bias_cents'])
            db.session.add(config)
        else:
            # Mise à jour
            config.ratio_percent = data['ratio_percent']
            config.bias_cents = data['bias_cents']
            
        db.session.commit()
        return config.to_dict()

    # 3. Fonction de calcul pour d'autres services (Listing, Purchase, Browse)
    @staticmethod
    def calculate_totals(price_cents: int, shipping_cents: int, config_data: dict = None):
        if not config_data:
            config_data = BuyerProtectionService.get_config()
            
        ratio = config_data['ratio_percent']
        bias = config_data['bias_cents']
        
        # Formule normative du Tier A:
        # percent_part = round_half_up(P * r / 100)
        # insurance_part_cents = percent_part + b
        
        percent_part = round_half_up(price_cents * ratio / 100.0)
        insurance_part_cents = percent_part + bias
        total_cents = price_cents + shipping_cents + insurance_part_cents
        
        return {
            "insurance_part_cents": insurance_part_cents,
            "total_cents": total_cents
        }