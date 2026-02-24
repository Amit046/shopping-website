# ShopFlask - Flask E-Commerce Website

## 🚀 Quick Setup

### 1. Create & activate a virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

---

## 🔑 Default Admin Account
- **Email:** admin@shop.com
- **Password:** admin123
- **Admin Panel:** http://127.0.0.1:5000/admin

---

## 📁 Project Structure

```
ecommerce/
│
├── app.py           → Main Flask app, all routes
├── models.py        → SQLAlchemy database models
├── forms.py         → WTForms form classes
├── requirements.txt → Python dependencies
│
├── templates/
│   ├── base.html             → Base layout (navbar, footer)
│   ├── index.html            → Homepage with hero + featured products
│   ├── login.html            → Login page
│   ├── register.html         → Register page
│   ├── products.html         → Product listing + search + filter
│   ├── product_detail.html   → Single product view
│   ├── cart.html             → Shopping cart
│   ├── checkout.html         → Checkout form
│   ├── order_history.html    → User order history
│   ├── admin_dashboard.html  → Admin panel
│   └── admin_product_form.html → Add/Edit product form
│
└── static/
    ├── css/style.css  → Custom styles
    └── js/main.js     → Auto-dismiss alerts
```

---

## ✅ Features
- User registration, login, logout (Flask-Login + password hashing)
- Product listing with category filter and search
- Product detail page with quantity selector
- Add to cart, update quantity, remove items
- Checkout and order placement
- Order history page
- Admin panel: add, edit, delete products + view orders
- Database auto-seeded with 8 sample products + admin user
