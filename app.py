from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)

app.config["SECRET_KEY"] = "online-store-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://postgres:Postgres%4007@localhost:5432/online_store"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------
# USER MODEL
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")


# -------------------------
# PRODUCT MODEL
# -------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(300))


# -------------------------
# ORDER MODEL
# -------------------------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Order Placed")


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    products = Product.query.all()
    return render_template("products.html", products=products)


# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "Username already exists!"

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password,
            role="user"
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["username"] = user.username
            session["role"] = user.role

            if user.role == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("home"))

        return "Invalid username or password!"

    return render_template("login.html")


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# -------------------------
# CART
# -------------------------
@app.route("/cart")
def cart():

    cart = session.get("cart", [])

    products = Product.query.filter(Product.id.in_(cart)).all() if cart else []

    total = sum(product.price for product in products)

    return render_template(
        "cart.html",
        products=products,
        total=total
    )


@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):

    if "username" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", [])

    cart.append(product_id)

    session["cart"] = cart

    return redirect(url_for("cart"))


# -------------------------
# CHECKOUT
# -------------------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    if "username" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", [])

    products = Product.query.filter(Product.id.in_(cart)).all()

    total = sum(product.price for product in products)

    if request.method == "POST":

        order = Order(
            username=session["username"],
            total=total,
            status="Order Placed"
        )

        db.session.add(order)
        db.session.commit()

        session["cart"] = []

        return redirect(url_for("orders"))

    return render_template(
        "checkout.html",
        products=products,
        total=total
    )


# -------------------------
# ORDERS
# -------------------------
@app.route("/orders")
def orders():

    if "username" not in session:
        return redirect(url_for("login"))

    user_orders = Order.query.filter_by(
        username=session["username"]
    ).all()

    return render_template(
        "orders.html",
        orders=user_orders
    )


# -------------------------
# ADMIN
# -------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if session.get("role") != "admin":
        return "Access denied!"

    # Add new product
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price"))
        image = request.form.get("image", "")

        product = Product(
            name=name,
            description=description,
            price=price,
            image=image
        )

        db.session.add(product)
        db.session.commit()

        return redirect(url_for("admin"))

    # Get products and orders
    products = Product.query.all()
    orders = Order.query.all()

    return render_template(
        "admin.html",
        products=products,
        orders=orders
    )

# -------------------------
# ADD PRODUCT
# -------------------------
@app.route("/admin/add", methods=["POST"])
def add_product():

    if session.get("role") != "admin":
        return "Access denied!"

    name = request.form["name"]
    description = request.form["description"]
    price = float(request.form["price"])
    image = request.form["image"]

    product = Product(
        name=name,
        description=description,
        price=price,
        image=image
    )

    db.session.add(product)
    db.session.commit()

    return redirect(url_for("admin"))


# -------------------------
# UPDATE ORDER
# -------------------------
@app.route("/admin/order/<int:order_id>", methods=["POST"])
def update_order(order_id):

    if session.get("role") != "admin":
        return "Access denied!"

    order = Order.query.get_or_404(order_id)

    order.status = request.form["status"]

    db.session.commit()

    return redirect(url_for("admin"))

# -------------------------
# REST APIs
# -------------------------

# Get all products
@app.route("/api/products", methods=["GET"])
def api_products():

    products = Product.query.all()

    return jsonify([
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image": product.image
        }
        for product in products
    ])


# Get one product
@app.route("/api/products/<int:product_id>", methods=["GET"])
def api_product(product_id):

    product = Product.query.get_or_404(product_id)

    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "image": product.image
    })


# Add product through API
@app.route("/api/products", methods=["POST"])
def api_add_product():

    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()

    product = Product(
        name=data["name"],
        description=data.get("description", ""),
        price=float(data["price"]),
        image=data.get("image", "")
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({
        "message": "Product added successfully",
        "product_id": product.id
    }), 201


# Update product through API
@app.route("/api/products/<int:product_id>", methods=["PUT"])
def api_update_product(product_id):

    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    product = Product.query.get_or_404(product_id)

    data = request.get_json()

    product.name = data.get("name", product.name)
    product.description = data.get(
        "description",
        product.description
    )
    product.price = float(
        data.get("price", product.price)
    )
    product.image = data.get(
        "image",
        product.image
    )

    db.session.commit()

    return jsonify({
        "message": "Product updated successfully"
    })


# Delete product through API
@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def api_delete_product(product_id):

    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    product = Product.query.get_or_404(product_id)

    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "message": "Product deleted successfully"
    })


# Get all orders - Admin
@app.route("/api/orders", methods=["GET"])
def api_orders():

    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    orders = Order.query.all()

    return jsonify([
        {
            "id": order.id,
            "username": order.username,
            "total": order.total,
            "status": order.status
        }
        for order in orders
    ])


# Update order status - Admin
@app.route("/api/orders/<int:order_id>", methods=["PUT"])
def api_update_order(order_id):

    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    order = Order.query.get_or_404(order_id)

    data = request.get_json()

    order.status = data.get(
        "status",
        order.status
    )

    db.session.commit()

    return jsonify({
        "message": "Order status updated successfully"
    })
    
# -------------------------
# CREATE DATABASE
# -------------------------
with app.app_context():
    db.create_all()

    # Create default admin
    admin_user = User.query.filter_by(username="admin").first()

    if not admin_user:
        admin_user = User(
            username="admin",
            password=generate_password_hash("admin123"),
            role="admin"
        )

        db.session.add(admin_user)
        db.session.commit()


# -------------------------
# RUN APPLICATION
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)