import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# =========================
# Page Settings
# =========================
st.set_page_config(
    page_title="Online Store",
    page_icon="🛒",
    layout="wide"
)

DB_NAME = "store.db"


# =========================
# Database
# =========================
def get_connection():
    return sqlite3.connect(DB_NAME)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    conn = get_connection()
    cur = conn.cursor()

    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Products
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            inventory INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Orders
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Order Items
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Create default admin
    cur.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    )

    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            ("admin", hash_password("admin123"), "admin")
        )

    # Create demo products if database is empty
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]

    if count == 0:
        products = [
            ("Classic T-Shirt", "Comfortable cotton T-shirt", 499, 20),
            ("Hoodie", "Warm and comfortable hoodie", 899, 15),
            ("Sneakers", "Everyday casual sneakers", 1299, 10),
            ("Backpack", "Simple school backpack", 699, 12)
        ]

        cur.executemany(
            """
            INSERT INTO products
            (name, description, price, inventory)
            VALUES (?, ?, ?, ?)
            """,
            products
        )

    conn.commit()
    conn.close()


init_database()


# =========================
# Session State
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

if "cart" not in st.session_state:
    st.session_state.cart = {}


# =========================
# Login / Register
# =========================
def login(username, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT username, role
        FROM users
        WHERE username = ? AND password = ?
        """,
        (username, hash_password(password))
    )

    user = cur.fetchone()
    conn.close()

    if user:
        st.session_state.logged_in = True
        st.session_state.username = user[0]
        st.session_state.role = user[1]
        return True

    return False


def register(username, password):
    if not username or not password:
        return False, "Username and password cannot be empty."

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            (username, hash_password(password), "customer")
        )

        conn.commit()
        return True, "Account created successfully!"

    except sqlite3.IntegrityError:
        return False, "Username already exists."

    finally:
        conn.close()


# =========================
# Logout
# =========================
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.cart = {}
    st.rerun()


# =========================
# Login Page
# =========================
def login_page():

    st.title("🛒 Online Store")
    st.write("Welcome to our online shopping website!")

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    with tab1:
        st.subheader("Login")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login", use_container_width=True):

            if login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect username or password.")

        st.info(
            "Demo Admin Account: username = admin, password = admin123"
        )

    with tab2:
        st.subheader("Create Customer Account")

        new_username = st.text_input(
            "New Username",
            key="register_username"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="register_password"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            success, message = register(
                new_username,
                new_password
            )

            if success:
                st.success(message)
            else:
                st.error(message)


# =========================
# Product Functions
# =========================
def get_products():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, description, price, inventory
        FROM products
        ORDER BY id DESC
    """)

    products = cur.fetchall()
    conn.close()

    return products


def add_product(name, description, price, inventory):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO products
        (name, description, price, inventory)
        VALUES (?, ?, ?, ?)
        """,
        (name, description, price, inventory)
    )

    conn.commit()
    conn.close()


def update_product(product_id, name, description, price, inventory):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE products
        SET name = ?,
            description = ?,
            price = ?,
            inventory = ?
        WHERE id = ?
        """,
        (
            name,
            description,
            price,
            inventory,
            product_id
        )
    )

    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()


# =========================
# Customer Store
# =========================
def customer_page():

    st.title("🛍️ Online Store")

    col1, col2 = st.columns([4, 1])

    with col1:
        st.write(
            f"Welcome, **{st.session_state.username}**!"
        )

    with col2:
        if st.button("Logout"):
            logout()

    st.divider()

    menu = st.radio(
        "Menu",
        [
            "🛍️ Products",
            "🛒 Shopping Cart",
            "📋 Order History"
        ],
        horizontal=True
    )

    if menu == "🛍️ Products":
        show_products()

    elif menu == "🛒 Shopping Cart":
        show_cart()

    elif menu == "📋 Order History":
        show_order_history()


def show_products():

    st.header("🛍️ Products")

    products = get_products()

    if not products:
        st.info("No products available.")
        return

    cols = st.columns(2)

    for index, product in enumerate(products):

        product_id, name, description, price, inventory = product

        with cols[index % 2]:

            with st.container(border=True):

                st.subheader(name)

                st.write(description)

                st.write(f"💰 Price: **${price:.2f}**")

                if inventory > 0:
                    st.write(
                        f"📦 Stock: **{inventory}**"
                    )

                    quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        max_value=inventory,
                        value=1,
                        key=f"qty_{product_id}"
                    )

                    if st.button(
                        "Add to Cart 🛒",
                        key=f"add_{product_id}",
                        use_container_width=True
                    ):

                        current = st.session_state.cart.get(
                            product_id,
                            0
                        )

                        if current + quantity <= inventory:
                            st.session_state.cart[
                                product_id
                            ] = current + quantity

                            st.success(
                                "Added to cart!"
                            )
                        else:
                            st.error(
                                "Not enough inventory."
                            )

                else:
                    st.error("Out of stock")


# =========================
# Shopping Cart
# =========================
def show_cart():

    st.header("🛒 Shopping Cart")

    cart = st.session_state.cart

    if not cart:
        st.info("Your cart is empty.")
        return

    products = get_products()

    product_dict = {
        product[0]: product
        for product in products
    }

    total = 0

    for product_id, quantity in list(cart.items()):

        if product_id not in product_dict:
            continue

        product = product_dict[product_id]

        name = product[1]
        price = product[3]
        inventory = product[4]

        subtotal = price * quantity
        total += subtotal

        col1, col2, col3, col4 = st.columns(
            [3, 1, 1, 1]
        )

        with col1:
            st.write(f"**{name}**")

        with col2:
            st.write(f"${price:.2f}")

        with col3:
            st.write(f"Qty: {quantity}")

        with col4:
            if st.button(
                "Remove",
                key=f"remove_{product_id}"
            ):
                del st.session_state.cart[
                    product_id
                ]
                st.rerun()

    st.divider()

    st.subheader(
        f"Total: ${total:.2f}"
    )

    st.write("### 💳 Checkout")

    payment_method = st.selectbox(
        "Payment Method",
        [
            "Credit Card",
            "Debit Card",
            "Cash on Delivery"
        ]
    )

    if payment_method in [
        "Credit Card",
        "Debit Card"
    ]:

        card_number = st.text_input(
            "Card Number",
            placeholder="1234 5678 9012 3456"
        )

        card_name = st.text_input(
            "Card Holder Name"
        )

    if st.button(
        "Complete Order 💳",
        use_container_width=True
    ):

        complete_order(
            total,
            payment_method
        )


# =========================
# Complete Order
# =========================
def complete_order(total, payment_method):

    conn = get_connection()
    cur = conn.cursor()

    try:

        # Check inventory again before purchase
        for product_id, quantity in st.session_state.cart.items():

            cur.execute(
                """
                SELECT name, price, inventory
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            )

            product = cur.fetchone()

            if product is None:
                raise Exception(
                    "A product no longer exists."
                )

            name, price, inventory = product

            if quantity > inventory:
                raise Exception(
                    f"Not enough stock for {name}."
                )

        # Create order
        cur.execute(
            """
            INSERT INTO orders
            (username, total, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                st.session_state.username,
                total,
                "Completed",
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        order_id = cur.lastrowid

        # Save order items + reduce inventory
        for product_id, quantity in st.session_state.cart.items():

            cur.execute(
                """
                SELECT name, price
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            )

            product = cur.fetchone()

            name, price = product

            cur.execute(
                """
                INSERT INTO order_items
                (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    product_id,
                    name,
                    quantity,
                    price
                )
            )

            cur.execute(
                """
                UPDATE products
                SET inventory = inventory - ?
                WHERE id = ?
                """,
                (
                    quantity,
                    product_id
                )
            )

        conn.commit()

        st.session_state.cart = {}

        st.success(
            f"🎉 Order #{order_id} completed!"
        )

        st.info(
            f"Payment method: {payment_method}"
        )

    except Exception as e:

        conn.rollback()

        st.error(
            f"Order failed: {e}"
        )

    finally:
        conn.close()


# =========================
# Order History
# =========================
def show_order_history():

    st.header("📋 Order History")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, total, status, created_at
        FROM orders
        WHERE username = ?
        ORDER BY id DESC
        """,
        (st.session_state.username,)
    )

    orders = cur.fetchall()

    conn.close()

    if not orders:
        st.info("You have no orders yet.")
        return

    for order in orders:

        order_id, total, status, created_at = order

        with st.expander(
            f"Order #{order_id} — ${total:.2f}"
        ):

            st.write(f"Status: {status}")
            st.write(f"Date: {created_at}")

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT product_name, quantity, price
                FROM order_items
                WHERE order_id = ?
                """,
                (order_id,)
            )

            items = cur.fetchall()
            conn.close()

            for item in items:

                name, quantity, price = item

                st.write(
                    f"- {name} × {quantity} "
                    f"(${price:.2f} each)"
                )


# =========================
# Admin Page
# =========================
def admin_page():

    st.title("👑 Admin Dashboard")

    col1, col2 = st.columns([4, 1])

    with col1:
        st.write(
            f"Logged in as **{st.session_state.username}**"
        )

    with col2:
        if st.button("Logout"):
            logout()

    st.divider()

    menu = st.radio(
        "Admin Menu",
        [
            "📦 Manage Products",
            "📊 Inventory",
            "📋 All Orders"
        ],
        horizontal=True
    )

    if menu == "📦 Manage Products":
        manage_products()

    elif menu == "📊 Inventory":
        inventory_page()

    elif menu == "📋 All Orders":
        all_orders()


# =========================
# Manage Products
# =========================
def manage_products():

    st.header("📦 Manage Products")

    st.subheader("➕ Add Product")

    with st.form("add_product_form"):

        name = st.text_input("Product Name")

        description = st.text_area(
            "Description"
        )

        price = st.number_input(
            "Price",
            min_value=0.0,
            value=10.0
        )

        inventory = st.number_input(
            "Inventory",
            min_value=0,
            value=10
        )

        submitted = st.form_submit_button(
            "Add Product"
        )

        if submitted:

            if not name:
                st.error(
                    "Product name is required."
                )
            else:

                add_product(
                    name,
                    description,
                    price,
                    inventory
                )

                st.success(
                    "Product added successfully!"
                )

                st.rerun()

    st.divider()

    st.subheader("✏️ Edit / Delete Products")

    products = get_products()

    for product in products:

        product_id, name, description, price, inventory = product

        with st.expander(
            f"{name} — ${price:.2f}"
        ):

            new_name = st.text_input(
                "Name",
                value=name,
                key=f"name_{product_id}"
            )

            new_description = st.text_area(
                "Description",
                value=description,
                key=f"description_{product_id}"
            )

            new_price = st.number_input(
                "Price",
                min_value=0.0,
                value=float(price),
                key=f"price_{product_id}"
            )

            new_inventory = st.number_input(
                "Inventory",
                min_value=0,
                value=int(inventory),
                key=f"inventory_{product_id}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Save Changes",
                    key=f"save_{product_id}",
                    use_container_width=True
                ):

                    update_product(
                        product_id,
                        new_name,
                        new_description,
                        new_price,
                        new_inventory
                    )

                    st.success(
                        "Product updated!"
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "Delete Product",
                    key=f"delete_{product_id}",
                    use_container_width=True
                ):

                    delete_product(product_id)

                    st.success(
                        "Product deleted!"
                    )

                    st.rerun()


# =========================
# Inventory
# =========================
def inventory_page():

    st.header("📊 Inventory Management")

    products = get_products()

    for product in products:

        product_id, name, description, price, inventory = product

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**{name}**")

        with col2:
            st.write(
                f"Price: ${price:.2f}"
            )

        with col3:
            if inventory == 0:
                st.error("OUT OF STOCK")
            elif inventory <= 5:
                st.warning(
                    f"Low stock: {inventory}"
                )
            else:
                st.success(
                    f"Stock: {inventory}"
                )


# =========================
# All Orders
# =========================
def all_orders():

    st.header("📋 All Customer Orders")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, total, status, created_at
        FROM orders
        ORDER BY id DESC
        """
    )

    orders = cur.fetchall()

    conn.close()

    if not orders:
        st.info("No orders yet.")
        return

    for order in orders:

        order_id, username, total, status, created_at = order

        with st.expander(
            f"Order #{order_id} — {username} — ${total:.2f}"
        ):

            st.write(
                f"Customer: {username}"
            )

            st.write(
                f"Total: ${total:.2f}"
            )

            st.write(
                f"Status: {status}"
            )

            st.write(
                f"Date: {created_at}"
            )


# =========================
# Main App
# =========================
if not st.session_state.logged_in:

    login_page()

else:

    if st.session_state.role == "admin":
        admin_page()

    else:
        customer_page()
