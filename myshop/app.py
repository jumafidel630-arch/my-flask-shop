import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-this-later'

# Database Configuration (Uses Render's cloud PostgreSQL database)
# Falls back to a local file if database URL is missing
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shop.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==========================================
# DATABASE MODELS (TABLES)
# ==========================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default="General")
    image_url = db.Column(db.String(500), default="https://unsplash.com")
    description = db.Column(db.Text, default="High quality product.")

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_email = db.Column(db.String(150), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)

# Temporary in-memory cart session (for demonstration)
cart = []

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================================
# HTML VISUAL TEMPLATES (MOBILE RESPONSIVE CSS)
# ==========================================
BASE_CSS = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    * { box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }
    body { background: #f4f6f9; color: #333; padding-bottom: 50px; }
    .navbar { background: #1a252f; padding: 15px; display: flex; justify-content: space-between; align-items: center; color: white; wrap: wrap; }
    .navbar a { color: white; text-decoration: none; margin: 0 10px; font-weight: bold; }
    .container { max-width: 1200px; margin: 20px auto; padding: 0 15px; }
    .search-box { width: 100%; max-width: 500px; display: flex; margin: 20px auto; }
    .search-box input { flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 4px 0 0 4px; font-size: 16px; }
    .search-box button { padding: 12px 20px; background: #e67e22; border: none; color: white; font-weight: bold; border-radius: 0 4px 4px 0; cursor: pointer; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }
    .card { background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; padding: 15px; display: flex; flex-direction: column; justify-content: space-between; transition: 0.2s; }
    .card:hover { transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
    .card img { width: 100%; height: 200px; object-fit: cover; border-radius: 6px; }
    .price { font-size: 18px; color: #27ae60; font-weight: bold; margin: 10px 0; }
    .btn { display: inline-block; width: 100%; background: #2ecc71; color: white; text-align: center; padding: 12px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; text-decoration: none; }
    .btn-admin { background: #e74c3c; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
    .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
    .alert { padding: 12px; background: #f8d7da; color: #721c24; margin-bottom: 15px; border-radius: 4px; border-left: 5px solid #dc3545; }
    .badge { background: #e67e22; color: white; padding: 2px 8px; border-radius: 50%; font-size: 12px; }
</style>
"""

DASHBOARD_HTML = BASE_CSS + """
<!DOCTYPE html>
<html>
<head><title>JumaShop - Modern E-Commerce</title></head>
<body>
<div class="navbar">
    <h2>🛍️ JumaShop</h2>
    <div>
        <a href="/">Home</a>
        <a href="/cart">Cart <span class="badge">{{ cart_count }}</span></a>
        {% if current_user.is_authenticated %}
            {% if current_user.is_admin %}<a href="/admin" style="color: #f1c40f;">👑 Admin</a>{% endif %}
            <a href="/logout">Logout ({{ current_user.email }})</a>
        {% else %}
            <a href="/login">Login</a>
            <a href="/register">Register</a>
        {% endif %}
    </div>
</div>

<div class="container">
    <!-- Automated Search Box -->
    <form method="GET" class="search-box">
        <input type="text" name="search" placeholder="Search brands, products, categories...">
        <button type="submit">Search</button>
    </form>

    {% with messages = get_flashed_messages() %}
      {% if messages %}{% for m in messages %}<div class="alert">{{ m }}</div>{% endfor %}{% endif %}
    {% endwith %}

    <h2>🔥 Featured Products</h2>
    <div class="grid">
        {% for product in products %}
        <div class="card">
            <div>
                <img src="{{ product.image_url }}" alt="Product Image">
                <h3 style="margin-top:10px;">{{ product.name }}</h3>
                <p style="color: #7f8c8d; font-size: 13px; margin: 5px 0;">Category: {{ product.category }}</p>
                <p style="font-size: 14px; margin-bottom:10px;">{{ product.description }}</p>
            </div>
            <div>
                <p class="price">KSh {{ "{:,.2f}".format(product.price) }}</p>
                <a href="/add/{{ product.id }}" class="btn">🛒 Add to Cart</a>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
</body>
</html>
"""

CART_HTML = BASE_CSS + """
<!DOCTYPE html>
<html>
<head><title>Your Cart - Secure Checkout</title></head>
<body>
<div class="navbar"><h2>🛡️ Secure Checkout</h2><a href="/">⬅️ Continue Shopping</a></div>
<div class="container" style="max-width: 600px;">
    <h2>Your Shopping Cart</h2>
    {% if not cart %}
        <p style="margin-top:20px;">Your cart is empty.</p>
    {% else %}
        {% for item in cart %}
            <div class="card" style="flex-direction: row; margin: 10px 0; padding: 10px;">
                <h4>{{ item.name }}</h4>
                <p class="price" style="margin:0;">KSh {{ "{:,.2f}".format(item.price) }}</p>
            </div>
        {% endfor %}
        <h3 style="margin-top:20px; text-align: right;">Total: KSh {{ "{:,.2f}".format(total) }}</h3>
        
        <!-- Trust Badge & Secure Checkout -->
        <div style="background:#e8f8f5; padding:15px; border-radius:6px; margin:20px 0; border: 1px solid #2ecc71;">
            <p style="color:#27ae60; font-weight:bold;">🔒 SSL Encrypted Checkout</p>
            <p style="font-size:12px; color:#7f8c8d;">Your personal details are encrypted and safe.</p>
        </div>

        <form action="/checkout" method="POST">
            <div class="form-group">
                <label>M-Pesa Mobile Number for Payment</label>
                <input type="text" name="phone" placeholder="e.g. 0712345678" required>
            </div>
            <button type="submit" class="btn" style="background:#e67e22;">Complete Payment (STK Push)</button>
        </form>
    {% endif %}
</div>
</body>
</html>
"""

ADMIN_HTML = BASE_CSS + """
<!DOCTYPE html>
<html>
<head><title>Management Control Board</title></head>
<body>
<div class="navbar"><h2>👑 System Admin Control Panel</h2><a href="/">Back to Shop Store</a></div>
<div class="container" style="max-width: 700px;">
    <h2>Add New Stock Product Item Item</h2>
    <form method="POST" style="background:white; padding:20px; border-radius:8px; margin-top:15px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
        <div class="form-group"><label>Product Name</label><input type="text" name="name" required></div>
        <div class="form-group"><label>Price (KSh)</label><input type="number" name="price" required></div>
        <div class="form-group"><label>Category</label><input type="text" name="category" placeholder="e.g. Electronics, Fashion" required></div>
        <div class="form-group"><label>Product Image Link URL</label><input type="text" name="image_url"></div>
        <div class="form-group"><label>Product Description</label><textarea name="description" rows="3"></textarea></div>
        <button type="submit" class="btn btn-admin">🚀 Publish Product Live</button>
    </form>
</div>
</body>
</html>
"""

LOGIN_HTML = BASE_CSS + """
<!DOCTYPE html>
<html>
<head><title>Account Sign In</title></head>
<body>
<div class="container" style="max-width: 400px; margin-top:100px;">
    <h2>Secure User Login</h2>
    <form method="POST" style="background:white; padding:20px; border-radius:8px; margin-top:15px;">
        {% with messages = get_flashed_messages() %}
          {% if messages %}{% for m in messages %}<div class="alert">{{ m }}</div>{% endfor %}{% endif %}
        {% endwith %}
        <div class="form-group"><label>Email Address</label><input type="email" name="email" required></div>
        <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
        <button type="submit" class="btn">Sign In</button>

