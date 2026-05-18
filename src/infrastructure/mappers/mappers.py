from src.domain.entities.entities import (
    Product, Stock, User, Cart, CartItem, Order, OrderItem
)
from src.domain.value_objects.value_objects import Email, Money, Quantity, Sku
from src.infrastructure.database.models import (
    ProductModel, StockModel, UserModel, CartModel, CartItemModel,
    OrderModel, OrderItemModel
)


class ProductMapper:
    @staticmethod
    def from_orm(orm_product: ProductModel) -> Product:
        return Product(
            id=orm_product.id,
            name=orm_product.name,
            sku=Sku(orm_product.sku),
            price=Money(float(orm_product.price)),
            category_id=orm_product.category_id
        )

    @staticmethod
    def to_orm(domain_product: Product) -> ProductModel:
        return ProductModel(
            id=domain_product.id,
            name=domain_product.name,
            sku=domain_product.sku.value,
            price=domain_product.price.amount,
            category_id=domain_product.category_id
        )


class StockMapper:
    @staticmethod
    def from_orm(orm_stock: StockModel) -> Stock:
        return Stock(
            id=orm_stock.id,
            product_id=orm_stock.product_id,
            quantity=Quantity(float(orm_stock.quantity))
        )

    @staticmethod
    def to_orm(domain_stock: Stock) -> StockModel:
        return StockModel(
            id=domain_stock.id,
            product_id=domain_stock.product_id,
            quantity=int(domain_stock.quantity.value)
        )


class UserMapper:
    @staticmethod
    def from_orm(orm_user: UserModel) -> User:
        return User(
            id=orm_user.id,
            email=Email(orm_user.email),
            username=orm_user.username,
            password_hash=orm_user.password_hash,
            group_id=orm_user.group_id
        )

    @staticmethod
    def to_orm(domain_user: User) -> UserModel:
        return UserModel(
            id=domain_user.id,
            email=domain_user.email.value,
            username=domain_user.username,
            password_hash=domain_user.password_hash,
            group_id=domain_user.group_id
        )


class CartItemMapper:
    @staticmethod
    def from_orm(orm_item: CartItemModel) -> CartItem:
        return CartItem(
            id=orm_item.id,
            product_id=orm_item.product_id,
            quantity=Quantity(float(orm_item.quantity))
        )

    @staticmethod
    def to_orm(domain_item: CartItem) -> CartItemModel:
        return CartItemModel(
            id=domain_item.id,
            product_id=domain_item.product_id,
            quantity=int(domain_item.quantity.value)
        )


class CartMapper:
    @staticmethod
    def from_orm(orm_cart: CartModel) -> Cart:
        items = [CartItemMapper.from_orm(item) for item in orm_cart.items]
        return Cart(
            id=orm_cart.id,
            user_id=orm_cart.user_id,
            items=items
        )

    @staticmethod
    def to_orm(domain_cart: Cart) -> CartModel:
        items = [CartItemMapper.to_orm(item) for item in domain_cart.items]
        return CartModel(
            id=domain_cart.id,
            user_id=domain_cart.user_id,
            items=items
        )


class OrderItemMapper:
    @staticmethod
    def from_orm(orm_item: OrderItemModel) -> OrderItem:
        return OrderItem(
            id=orm_item.id,
            product_id=orm_item.product_id,
            quantity=Quantity(float(orm_item.quantity)),
            price_at_purchase=Money(float(orm_item.price_at_purchase))
        )

    @staticmethod
    def to_orm(domain_item: OrderItem) -> OrderItemModel:
        return OrderItemModel(
            id=domain_item.id,
            product_id=domain_item.product_id,
            quantity=float(domain_item.quantity.value),
            price_at_purchase=domain_item.price_at_purchase.amount
        )


class OrderMapper:
    @staticmethod
    def from_orm(orm_order: OrderModel) -> Order:
        items = [OrderItemMapper.from_orm(item) for item in orm_order.items]
        return Order(
            id=orm_order.id,
            user_id=orm_order.user_id,
            items=items,
            status=orm_order.status,
            total_price=Money(float(orm_order.total_price)),
            created_at=orm_order.created_at
        )

    @staticmethod
    def to_orm(domain_order: Order) -> OrderModel:
        items = [OrderItemMapper.to_orm(item) for item in domain_order.items]
        return OrderModel(
            id=domain_order.id,
            user_id=domain_order.user_id,
            items=items,
            status=domain_order.status,
            total_price=domain_order.total_price.amount,
            created_at=domain_order.created_at
        )
