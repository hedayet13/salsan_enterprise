from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class CarImage(db.Model):
    __tablename__ = "car_images"
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey("cars.id", ondelete="CASCADE"), index=True)
    url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0, index=True)

class Car(db.Model):
    __tablename__ = "cars"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    make = db.Column(db.String(80), index=True)
    model = db.Column(db.String(80), index=True)
    year = db.Column(db.Integer, index=True)
    price = db.Column(db.Integer, index=True)  # store in local currency integer
    auction_point = db.Column(db.String(20))
    mileage_km = db.Column(db.Integer, index=True)
    fuel_type = db.Column(db.String(50), index=True)  # Petrol, Diesel, Hybrid, Electric
    transmission = db.Column(db.String(50), index=True)  # Automatic, Manual
    body_type = db.Column(db.String(50), index=True)  # Sedan, SUV, etc.
    color = db.Column(db.String(50))
    location = db.Column(db.String(120))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    is_delivered = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    images = db.relationship(
        "CarImage",
        backref="car",
        cascade="all, delete-orphan",
        order_by="CarImage.sort_order",
        lazy="selectin",
    )

    @property
    def primary_image(self):
        """Prefer legacy image_url, else first extra image, else None."""
        return self.image_url or (self.images[0].url if self.images else None)

    

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "price": self.price,
            "mileage_km": self.mileage_km,
            "fuel_type": self.fuel_type,
            "transmission": self.transmission,
            "body_type": self.body_type,
            "color": self.color,
            "location": self.location,
            "description": self.description,
            "image_url": self.image_url,
            "is_delivered": self.is_delivered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, index=True)
