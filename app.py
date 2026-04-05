from flask import Flask, render_template, flash, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from datetime import datetime as dt
from form import RegisterForm, LoginForm
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from models import db, User, Menu, OrderItem, Order
from flask_migrate import Migrate
import os

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')

login_manager = LoginManager()
login_manager.init_app(app)
bootstrap = Bootstrap5(app)

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.context_processor
def inject_global_data():
    def get_cart_count():
        if not current_user.is_authenticated:
            return 0

        active_order = Order.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()

        if not active_order or not active_order.order_items:
            return 0

        return sum(item.quantity for item in active_order.order_items)

    return {
        'year': dt.now().year,
        'get_cart_count': get_cart_count
    }

@app.route('/')
def home():
    carousel_folder = 'static/assets/images/carousel'
    images = os.listdir(carousel_folder)
    return render_template('index.html', images=images, title='Flask Bites')


@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        try:
            result = db.session.execute(db.select(User).where(User.email == email))
            user = result.scalars().one()
        except NoResultFound:
            flash('Email not yet registered. Try registering first.', 'error')
        else:
            password = login_form.password.data
            if user.check_password(password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Incorrect password. Please try again.', 'error')
    return render_template('login.html', form=login_form, title='Login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        new_user = User(email=register_form.email.data, username=register_form.username.data)
        new_user.set_password(register_form.password.data)
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            flash('You already registered that email. Try logging in instead.', 'error')
            return redirect(url_for('login'))
        else:
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template('register.html', form=register_form, title='Register')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/menu')
def menu():
    stmt = select(Menu)
    all_items = db.session.execute(stmt).scalars().all()
    return render_template('menu.html', items=all_items, title='Menu')


@app.route('/bag')
@login_required
def bag():
    stmt = select(Order).where(Order.user_id == current_user.id).where(Order.status == 'pending')
    order: Order = db.session.execute(stmt).scalars().first()
    return render_template('bag.html', order=order, title='Bag')


@app.route('/add-item')
@login_required
def add_item():
    stmt = select(Order).where(Order.user_id == current_user.id).where(Order.status == 'pending')
    order: Order = db.session.execute(stmt).scalars().first()
    if not order:
        order = Order(status='pending', user=current_user)
        db.session.add(order)
        db.session.commit()

    menu_id = request.args.get('menu_id')
    menu: Menu = db.get_or_404(Menu, menu_id)

    stmt = select(OrderItem).where(OrderItem.order_id == order.id).where(OrderItem.menu_id == menu.id)
    order_item: OrderItem = db.session.execute(stmt).scalars().first()
    if order_item:
        order_item.quantity += 1
    else:
        order_item = OrderItem(quantity=1, price=menu.price, order=order, menu=menu)
        db.session.add(order_item)
    db.session.commit()

    return redirect(url_for('bag'))


@app.route('/increase-quantity')
@login_required
def increase_quantity():
    item_id = request.args.get('item_id')
    item = db.get_or_404(OrderItem, item_id)
    item.quantity += 1
    db.session.commit()

    return redirect(url_for('bag'))


@app.route('/decrease-quantity')
@login_required
def decrease_quantity():
    item_id = request.args.get('item_id')
    item = db.get_or_404(OrderItem, item_id)
    if item.quantity > 1:
        item.quantity -= 1
        db.session.commit()
    else:
        return redirect(url_for('delete_item', item_id=item_id))
    return redirect(url_for('bag'))


@app.route('/delete-item')
@login_required
def delete_item():
    item_id = request.args.get('item_id')
    item = db.get_or_404(OrderItem, item_id)
    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('bag'))


@app.route('/checkout')
@login_required
def checkout():
    order_id = request.args.get('order_id')
    order: Order = db.get_or_404(Order, order_id)
    order.status = 'completed'
    db.session.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
