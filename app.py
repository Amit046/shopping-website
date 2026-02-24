from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Category, Cart, CartItem, Order, OrderItem
from forms import RegisterForm, LoginForm, CheckoutForm, ProductForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Context Processor ────────────────────────────────────────────────────────
@app.context_processor
def inject_cart_count():
    count = 0
    if current_user.is_authenticated and current_user.cart:
        count = current_user.cart.count
    categories = Category.query.all()
    return dict(cart_count=count, all_categories=categories)


# ─── Auth Routes ──────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── Product Routes ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    featured = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    return render_template('index.html', products=featured)


@app.route('/products')
def products():
    category_slug = request.args.get('category')
    search = request.args.get('search', '').strip()
    query = Product.query

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=cat.id)
    else:
        cat = None

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products_list = query.all()
    return render_template('products.html', products=products_list, current_category=cat, search=search)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)


# ─── Cart Routes ──────────────────────────────────────────────────────────────
@app.route('/cart')
@login_required
def cart():
    cart = current_user.cart
    return render_template('cart.html', cart=cart)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))

    if not current_user.cart:
        user_cart = Cart(user_id=current_user.id)
        db.session.add(user_cart)
        db.session.flush()
    else:
        user_cart = current_user.cart

    item = CartItem.query.filter_by(cart_id=user_cart.id, product_id=product_id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=user_cart.id, product_id=product_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    flash(f'"{product.name}" added to cart!', 'success')
    return redirect(request.referrer or url_for('products'))


@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        abort(403)
    quantity = int(request.form.get('quantity', 1))
    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = quantity
    db.session.commit()
    flash('Cart updated.', 'info')
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


# ─── Order Routes ─────────────────────────────────────────────────────────────
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = current_user.cart
    if not cart or not cart.items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('products'))

    form = CheckoutForm()
    if form.validate_on_submit():
        order = Order(
            user_id=current_user.id,
            total_price=cart.total,
            address=form.address.data
        )
        db.session.add(order)
        db.session.flush()

        for item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)

        # Clear cart
        for item in list(cart.items):
            db.session.delete(item)

        db.session.commit()
        flash(f'Order #{order.id} placed successfully!', 'success')
        return redirect(url_for('order_history'))

    return render_template('checkout.html', form=form, cart=cart)


@app.route('/orders')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders)


# ─── Admin Routes ─────────────────────────────────────────────────────────────
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_dashboard.html', products=products, orders=orders)


@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            image_url=form.image_url.data,
            category_id=form.category_id.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_product_form.html', form=form, title='Add Product')


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.image_url = form.image_url.data
        product.category_id = form.category_id.data
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_product_form.html', form=form, title='Edit Product')


@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))


# ─── Database Seeder ──────────────────────────────────────────────────────────
def seed_database():
    if Category.query.first():
        return  # already seeded

    fashion = Category(name='Fashion', slug='fashion')
    electronics = Category(name='Electronics', slug='electronics')
    db.session.add_all([fashion, electronics])
    db.session.flush()

    products = [
        Product(name='Classic White T-Shirt', description='Comfortable 100% cotton tee.', price=19.99, stock=50,
                image_url='https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400', category_id=fashion.id),
        Product(name='Slim Fit Jeans', description='Modern slim fit denim jeans.', price=49.99, stock=30,
                image_url='https://images.unsplash.com/photo-1542272604-787c3835535d?w=400', category_id=fashion.id),
        Product(name='Running Sneakers', description='Lightweight performance sneakers.', price=79.99, stock=20,
                image_url='https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400', category_id=fashion.id),
        Product(name='Leather Jacket', description='Premium genuine leather jacket.', price=199.99, stock=15,
                image_url='https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400', category_id=fashion.id),
        Product(name='Wireless Headphones', description='Noise-cancelling bluetooth headphones.', price=129.99, stock=25,
                image_url='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400', category_id=electronics.id),
        Product(name='Smartphone Stand', description='Adjustable aluminum phone stand.', price=24.99, stock=100,
                image_url='https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400', category_id=electronics.id),
        Product(name='Laptop Sleeve', description='15" water-resistant laptop sleeve.', price=34.99, stock=60,
                image_url='https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400', category_id=electronics.id),
        Product(name='USB-C Hub', description='7-in-1 multiport USB-C hub.', price=59.99, stock=40,
                image_url='https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400', category_id=electronics.id),
    ]
    db.session.add_all(products)

    # Create admin user
    admin = User(
        username='admin',
        email='admin@shop.com',
        password=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Database seeded! Admin: admin@shop.com / admin123")


def create_app():
    with app.app_context():
        db.create_all()
        seed_database()
    return app

if __name__ == '__main__':
    create_app()
    app.run(debug=True)