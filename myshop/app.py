from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

products = [
    {"id": 1, "name": "Laptop", "price": 50000},
    {"id": 2, "name": "Phone", "price": 25000},
    {"id": 3, "name": "Headphones", "price": 3000},
    {"id": 4, "name": "Keyboard", "price": 2000}
]

cart = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Shopping Website</title>
    <style>
        body {
            font-family: Arial;
            margin: 20px;
        }
        .navbar {
            background: #333;
            padding: 10px;
        }
        .navbar a {
            color: white;
            text-decoration: none;
            margin-right: 20px;
        }
        .product {
            border: 1px solid #ddd;
            padding: 10px;
            margin: 10px;
        }
        button {
            background: green;
            color: white;
            border: none;
            padding: 8px;
            cursor: pointer;
        }
    </style>
</head>
<body>

<div class="navbar">
    <a href="/">Dashboard</a>
    <a href="/cart">Cart ({{ cart_count }})</a>
</div>

<h1>Shopping Dashboard</h1>

<form method="GET">
    <input type="text" name="search" placeholder="Search products">
    <button type="submit">Search</button>
</form>

{% for product in products %}
<div class="product">
    <h3>{{ product.name }}</h3>
    <p>Price: KSh {{ product.price }}</p>
    <a href="/add/{{ product.id }}">
        <button>Add to Cart</button>
    </a>
</div>
{% endfor %}

</body>
</html>
"""

CART_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Cart</title>
</head>
<body>
    <h1>Your Cart</h1>

    {% for item in cart %}
        <p>{{ item.name }} - KSh {{ item.price }}</p>
    {% endfor %}

    <h3>Total: KSh {{ total }}</h3>

    <a href="/">Continue Shopping</a>
</body>
</html>
"""

@app.route("/")
def dashboard():
    search = request.args.get("search", "")

    filtered_products = [
        p for p in products
        if search.lower() in p["name"].lower()
    ]

    return render_template_string(
        HTML,
        products=filtered_products,
        cart_count=len(cart)
    )

@app.route("/add/<int:id>")
def add_to_cart(id):
    for product in products:
        if product["id"] == id:
            cart.append(product)
            break

    return redirect(url_for("dashboard"))

@app.route("/cart")
def view_cart():
    total = sum(item["price"] for item in cart)

    return render_template_string(
        CART_HTML,
        cart=cart,
        total=total
    )

if __name__ == "__main__":
    app.run(debug=True)