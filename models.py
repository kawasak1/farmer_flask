from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    profile_picture_url = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)

    # Relationships
    farmer = db.relationship('Farmer', uselist=False, back_populates='user')
    buyer = db.relationship('Buyer', uselist=False, back_populates='user')
    #products = db.relationship('Product', back_populates='farmer_user', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender', lazy='dynamic', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', back_populates='recipient', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')
    addresses = db.relationship('Address', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
  
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
  
    def get_id(self):
        return str(self.id)
  
    def __repr__(self):
        return f'<User {self.username}>'

# Farmer Model
class Farmer(db.Model):
    __tablename__ = 'farmers'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    farm_name = db.Column(db.String(100))
    farm_size = db.Column(db.Float)
    farm_address = db.Column(db.String(255))
    farm_description = db.Column(db.Text)
    farm_latitude = db.Column(db.Numeric(9,6))
    farm_longitude = db.Column(db.Numeric(9,6))
    crops_grown = db.Column(db.Text)  # Consider using JSON or ARRAY for multiple crops

    # Relationships
    user = db.relationship('User', back_populates='farmer', passive_deletes=True)
    products = db.relationship('Product', back_populates='farmer', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='farmer', lazy='dynamic')

    def __repr__(self):
        return f'<Farmer {self.user.username}>'

# Buyer Model
class Buyer(db.Model):
    __tablename__ = 'buyers'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    default_delivery_address = db.Column(db.String(255))
    preferred_payment_method = db.Column(db.String(50))

    # Relationships
    user = db.relationship('User', back_populates='buyer', passive_deletes=True)
    orders = db.relationship('Order', back_populates='buyer', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='reviewer', lazy='dynamic')
    offers = db.relationship('Offer', back_populates='buyer', lazy='dynamic')
    cart = db.relationship('Cart', uselist=False, back_populates='buyer')

    def __repr__(self):
        return f'<Buyer {self.user.username}>'

# Category Model
class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    # Relationships
    products = db.relationship('Product', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

# Product Model
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.user_id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10,2), nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    quantity_unit = db.Column(db.String(50), nullable=False)  # e.g., 'kg', 'lbs', 'pieces'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    farmer = db.relationship('Farmer', back_populates='products')
    #farmer_user = db.relationship('User', back_populates='products', foreign_keys=[farmer_id])
    category = db.relationship('Category', back_populates='products')
    images = db.relationship('ProductImage', back_populates='product', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True)
    order_items = db.relationship('OrderItem', back_populates='product', lazy='dynamic')
    offers = db.relationship('Offer', back_populates='product', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='product', lazy='dynamic')

    def __repr__(self):
        return f'<Product {self.name}>'

# ProductImage Model
class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    order_num = db.Column(db.Integer, default=1)

    # Relationships
    product = db.relationship('Product', back_populates='images')

    def __repr__(self):
        return f'<ProductImage {self.image_url}>'

# Cart Model
class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyers.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    buyer = db.relationship('Buyer', back_populates='cart')
    items = db.relationship('CartItem', back_populates='cart', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Cart {self.id} for Buyer {self.buyer_id}>'

#CartItem Model
class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cart = db.relationship('Cart', back_populates='items')
    product = db.relationship('Product')

    def __repr__(self):
        return f'<CartItem {self.id} in Cart {self.cart_id}>'

# Order Model
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyers.user_id'), nullable=False)
    total_amount = db.Column(db.Numeric(12,2), nullable=False)
    payment_status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'failed'
    payment_method = db.Column(db.String(50))
    delivery_address = db.Column(db.String(255))
    status = db.Column(db.String(50), default='placed')  # 'placed', 'confirmed', 'dispatched', 'delivered'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    buyer = db.relationship('Buyer', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order', lazy='dynamic')

    def __repr__(self):
        return f'<Order {self.id} by Buyer {self.buyer_id}>'

# OrderItem Model
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.user_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10,2), nullable=False)  # Price per unit at the time of order
    subtotal = db.Column(db.Numeric(12,2), nullable=False)

    # Relationships
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')
    farmer = db.relationship('Farmer')

    def __repr__(self):
        return f'<OrderItem {self.id} in Order {self.order_id}>'

# Message Model
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    seen_at = db.Column(db.DateTime)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_messages')

    def __repr__(self):
        return f'<Message from {self.sender_id} to {self.recipient_id}>'

# Offer Model
class Offer(db.Model):
    __tablename__ = 'offers'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyers.user_id'), nullable=False)
    offer_price = db.Column(db.Numeric(10,2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'accepted', 'rejected', 'countered'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', back_populates='offers')
    buyer = db.relationship('Buyer', back_populates='offers')

    def __repr__(self):
        return f'<Offer {self.id} on Product {self.product_id}>'

# Notification Model
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

# Address Model
class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address_type = db.Column(db.String(50), default='home')  # 'home', 'business', etc.
    street_address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(9,6))
    longitude = db.Column(db.Numeric(9,6))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='addresses')

    def __repr__(self):
        return f'<Address {self.id} for User {self.user_id}>'

# Review Model
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('buyers.user_id'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reviewer = db.relationship('Buyer', back_populates='reviews')
    farmer = db.relationship('Farmer', back_populates='reviews')
    product = db.relationship('Product', back_populates='reviews')

    def __repr__(self):
        return f'<Review {self.id} by Buyer {self.reviewer_id}>'

