class DomainError(Exception):
    """Base domain error"""
    pass


class InvalidEmailError(DomainError):
    """Email is invalid"""
    pass


class EmailAlreadyExistsError(DomainError):
    """User with this email already exists"""
    pass


class UsernameAlreadyExistsError(DomainError):
    """User with this username already exists"""
    pass


class InvalidProductError(DomainError):
    """Product data is invalid"""
    pass


class DuplicateSkuError(DomainError):
    """Product with this SKU already exists"""
    pass


class ProductNotFoundError(DomainError):
    """Product not found"""
    pass


class InsufficientStockError(DomainError):
    """Not enough stock for this product"""
    pass


class OrderNotFoundError(DomainError):
    """Order not found"""
    pass


class InvalidOrderStatusError(DomainError):
    """Invalid order status"""
    pass


class CartItemNotFoundError(DomainError):
    """Cart item not found"""
    pass
