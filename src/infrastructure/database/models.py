from datetime import datetime
from typing import List, Optional
from sqlalchemy import Integer, String, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_groups.id"))
    group: Mapped[Optional["UserGroupModel"]] = relationship(back_populates="users")

    cart: Mapped[Optional["CartModel"]] = relationship(back_populates="user", uselist=False)
    orders: Mapped[List["OrderModel"]] = relationship(back_populates="user")


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    users: Mapped[List["UserModel"]] = relationship(back_populates="group")


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    products: Mapped[List["ProductModel"]] = relationship(back_populates="category")


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    category: Mapped["CategoryModel"] = relationship(back_populates="products")
    stock: Mapped[Optional["StockModel"]] = relationship(
        back_populates="product", uselist=False
    )
    cart_items: Mapped[List["CartItemModel"]] = relationship(back_populates="product")
    order_items: Mapped[List["OrderItemModel"]] = relationship(back_populates="product")


class StockModel(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)
    quantity: Mapped[float] = mapped_column(Integer, default=0)

    product: Mapped["ProductModel"] = relationship(back_populates="stock")


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    user: Mapped["UserModel"] = relationship(back_populates="cart")
    items: Mapped[List["CartItemModel"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Integer, default=1)

    cart: Mapped["CartModel"] = relationship(back_populates="items")
    product: Mapped["ProductModel"] = relationship(back_populates="cart_items")


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    total_price: Mapped[float] = mapped_column(Numeric(10, 2))

    user: Mapped["UserModel"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItemModel"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Numeric(10, 3))
    price_at_purchase: Mapped[float] = mapped_column(Numeric(10, 2))

    order: Mapped["OrderModel"] = relationship(back_populates="items")
    product: Mapped["ProductModel"] = relationship(back_populates="order_items")
