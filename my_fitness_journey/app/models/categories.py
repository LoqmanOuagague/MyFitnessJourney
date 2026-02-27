from app.database.database import db
from sqlalchemy import CheckConstraint, ForeignKey


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    # Relation vers la catégorie parente
    parent = db.relationship("Category", remote_side=[id], backref="children")
    listings = db.relationship("Listing", backref="category", lazy=True)
    # Contraintes facultatives (ici, juste un exemple de structure propre)
    __table_args__ = (
        CheckConstraint("id >= 1", name="check_id_positive"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id
        }
