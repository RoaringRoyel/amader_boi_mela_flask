from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    profile_picture = db.Column(db.String(150), nullable=True, default="default.png")
    role = db.Column(db.String(50), nullable=False)  # 'buyer' or 'seller'

    # Relationships
    books = db.relationship('Book', back_populates='seller')
    reviews = db.relationship('Review', back_populates='user')
    carts = db.relationship('Cart', back_populates='user')
    blogs = db.relationship('Blog', back_populates='author')
    favorites = db.relationship('Favorite', back_populates='user')
    sales = db.relationship('Sale', back_populates='seller')

    # New relationship for book exchange requests
    exchange_requests = db.relationship('BookExchangeRequest', back_populates='user', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(150), nullable=True)
    price = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_used = db.Column(db.Boolean, default=False)  # Indicates if the book is used

    # Relationships
    seller = db.relationship('User', back_populates='books')
    reviews = db.relationship('Review', back_populates='book')
    cart_items = db.relationship('CartItem', back_populates='book')
    favorites = db.relationship('Favorite', back_populates='book')
    sales = db.relationship('Sale', back_populates='book')
    
    # Define the relationship with BookExchangeRequest
    exchange_requests = db.relationship('BookExchangeRequest', back_populates='book', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relationships
    user = db.relationship('User', back_populates='reviews')
    book = db.relationship('Book', back_populates='reviews')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relationships
    user = db.relationship('User', back_populates='carts')
    items = db.relationship('CartItem', back_populates='cart')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Relationships
    cart = db.relationship('Cart', back_populates='items')
    book = db.relationship('Book', back_populates='cart_items')

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    author = db.relationship('User', back_populates='blogs')

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    date_added = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relationships
    user = db.relationship('User', back_populates='favorites')
    book = db.relationship('Book', back_populates='favorites')

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False, default=1)
    date_sold = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relationships
    book = db.relationship('Book', back_populates='sales')
    seller = db.relationship('User', back_populates='sales')

class BookExchangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # 'Pending', 'Approved', 'Rejected'
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relationships
    user = db.relationship('User', back_populates='exchange_requests')
    book = db.relationship('Book', back_populates='exchange_requests')
