import pytest
from src.domain.value_objects.value_objects import Email, Money, Quantity, Sku
from src.domain.entities.entities import Product, Stock, Cart, CartItem, Order
from src.domain.errors.domain_errors import InsufficientStockError


class TestValueObjects:
    """Unit tests for value objects - no DB, no framework needed"""

    def test_email_valid(self):
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_email_invalid(self):
        with pytest.raises(ValueError):
            Email("invalid-email")

    def test_money_positive(self):
        money = Money(100.50)
        assert money.amount == 100.50

    def test_money_negative_fails(self):
        with pytest.raises(ValueError):
            Money(-10)

    def test_money_addition(self):
        m1 = Money(100)
        m2 = Money(50)
        result = m1 + m2
        assert result.amount == 150

    def test_money_multiplication(self):
        m = Money(100)
        result = m * 3
        assert result.amount == 300

    def test_quantity_valid(self):
        qty = Quantity(10)
        assert qty.value == 10

    def test_quantity_subtraction(self):
        q1 = Quantity(10)
        q2 = Quantity(3)
        result = q1 - q2
        assert result.value == 7

    def test_quantity_subtraction_insufficient(self):
        q1 = Quantity(3)
        q2 = Quantity(10)
        with pytest.raises(ValueError):
            q1 - q2

    def test_sku_valid(self):
        sku = Sku("SKU-123")
        assert sku.value == "SKU-123"

    def test_sku_empty_fails(self):
        with pytest.raises(ValueError):
            Sku("")


class TestProduct:
    """Unit tests for Product entity"""

    def test_product_creation(self):
        product = Product(
            id=1,
            name="Test Product",
            sku=Sku("SKU-001"),
            price=Money(99.99),
            category_id=1
        )
        assert product.name == "Test Product"
        assert product.sku.value == "SKU-001"

    def test_product_validation_empty_name(self):
        product = Product(
            id=1,
            name="",
            sku=Sku("SKU-001"),
            price=Money(99.99),
            category_id=1
        )
        with pytest.raises(ValueError):
            product.validate()

    def test_product_validation_negative_price(self):
        product = Product(
            id=1,
            name="Product",
            sku=Sku("SKU-001"),
            price=Money(0),
            category_id=1
        )
        with pytest.raises(ValueError):
            product.validate()


class TestStock:
    """Unit tests for Stock entity"""

    def test_stock_creation(self):
        stock = Stock(
            id=1,
            product_id=1,
            quantity=Quantity(100)
        )
        assert stock.quantity.value == 100

    def test_stock_reduce(self):
        stock = Stock(id=1, product_id=1, quantity=Quantity(100))
        stock.reduce(Quantity(30))
        assert stock.quantity.value == 70

    def test_stock_reduce_insufficient_fails(self):
        stock = Stock(id=1, product_id=1, quantity=Quantity(10))
        with pytest.raises(ValueError):
            stock.reduce(Quantity(20))

    def test_stock_increase(self):
        stock = Stock(id=1, product_id=1, quantity=Quantity(100))
        stock.increase(Quantity(50))
        assert stock.quantity.value == 150

    def test_stock_has_enough(self):
        stock = Stock(id=1, product_id=1, quantity=Quantity(100))
        assert stock.has_enough(Quantity(50)) is True
        assert stock.has_enough(Quantity(150)) is False


class TestCart:
    """Unit tests for Cart aggregate root"""

    def test_cart_creation(self):
        cart = Cart(id=1, user_id=1, items=[])
        assert cart.user_id == 1

    def test_cart_add_item(self):
        cart = Cart(id=1, user_id=1, items=[])
        cart.add_item(
            product_id=1,
            quantity=Quantity(5),
            price=Money(100)
        )
        assert len(cart.items) == 1
        assert cart.items[0].quantity.value == 5

    def test_cart_add_duplicate_item_increases_quantity(self):
        cart = Cart(id=1, user_id=1, items=[])
        cart.add_item(1, Quantity(5), Money(100))
        cart.add_item(1, Quantity(3), Money(100))
        assert len(cart.items) == 1
        assert cart.items[0].quantity.value == 8

    def test_cart_remove_item(self):
        cart = Cart(id=1, user_id=1, items=[])
        cart.add_item(1, Quantity(5), Money(100))
        cart.add_item(2, Quantity(3), Money(50))
        cart.remove_item(1)
        assert len(cart.items) == 1
        assert cart.items[0].product_id == 2

    def test_cart_clear(self):
        cart = Cart(id=1, user_id=1, items=[])
        cart.add_item(1, Quantity(5), Money(100))
        cart.add_item(2, Quantity(3), Money(50))
        cart.clear()
        assert len(cart.items) == 0

    def test_cart_total_price(self):
        cart = Cart(id=1, user_id=1, items=[])
        cart.add_item(1, Quantity(2), Money(100))  # 200
        cart.add_item(2, Quantity(3), Money(50))   # 150
        total = cart.total_price()
        assert total.amount == 350


class TestOrder:
    """Unit tests for Order aggregate root"""

    def test_order_creation(self):
        from datetime import datetime
        order = Order(
            id=1,
            user_id=1,
            items=[],
            status="pending",
            total_price=Money(500),
            created_at=datetime.utcnow()
        )
        assert order.user_id == 1
        assert order.status == "pending"

    def test_order_can_cancel_pending(self):
        from datetime import datetime
        order = Order(
            id=1,
            user_id=1,
            items=[],
            status="pending",
            total_price=Money(500),
            created_at=datetime.utcnow()
        )
        assert order.can_cancel() is True

    def test_order_cannot_cancel_shipped(self):
        from datetime import datetime
        order = Order(
            id=1,
            user_id=1,
            items=[],
            status="shipped",
            total_price=Money(500),
            created_at=datetime.utcnow()
        )
        assert order.can_cancel() is False

    def test_order_validation_empty_items(self):
        from datetime import datetime
        order = Order(
            id=1,
            user_id=1,
            items=[],
            status="pending",
            total_price=Money(500),
            created_at=datetime.utcnow()
        )
        with pytest.raises(ValueError):
            order.validate()

    def test_order_validation_invalid_status(self):
        from datetime import datetime
        from src.domain.entities.entities import OrderItem

        order = Order(
            id=1,
            user_id=1,
            items=[OrderItem(id=1, product_id=1, quantity=Quantity(1), price_at_purchase=Money(100))],
            status="invalid_status",
            total_price=Money(500),
            created_at=datetime.utcnow()
        )
        with pytest.raises(ValueError):
            order.validate()
