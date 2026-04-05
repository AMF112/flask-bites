from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from argon2 import PasswordHasher
from decimal import Decimal
from datetime import datetime


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
ph = PasswordHasher()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    orders: Mapped[list[Order]] = relationship(back_populates='user')

    def set_password(self, plaintext_password: str) -> None:
        self.password = ph.hash(plaintext_password)

    def check_password(self, plaintext_password: str) -> bool:
        assert isinstance(self.password, str)
        return ph.verify(self.password, plaintext_password)


class Menu(db.Model):
    __tablename__ = 'menus'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    img_url: Mapped[str] = mapped_column(String, nullable=False)

    order_items: Mapped[list[OrderItem]] = relationship(back_populates='menu')


class Order(db.Model):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    user: Mapped[User] = relationship(back_populates='orders')
    order_items: Mapped[list[OrderItem]] = relationship(back_populates='order')

    @property
    def total_price(self):
        return sum(item.price * item.quantity for item in self.order_items)


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey('orders.id'))
    menu_id: Mapped[int] = mapped_column(Integer, ForeignKey('menus.id'))

    __table_args__ = (
        UniqueConstraint('order_id', 'menu_id', name='uix_order_menu'),
    )

    order: Mapped[Order] = relationship(back_populates='order_items')
    menu: Mapped[Menu] = relationship(back_populates='order_items')
