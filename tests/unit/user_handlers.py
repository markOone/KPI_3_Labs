import pytest
from unittest.mock import AsyncMock, patch

from src.application.commands.user_commands import AddUserCommand, LoginUserCommand
# Уточніть шлях до файлу з вашими хендлерами, якщо він відрізняється
from src.application.commands.user_handlers import AddUserCommandHandler, LoginUserCommandHandler
from src.domain.entities.entities import User
from src.domain.value_objects.value_objects import Email
from src.domain.errors.domain_errors import (
    CredentialsError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.schemas.auth import UserResponseSchema

# ==========================================
# ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ ТЕСТІВ
# ==========================================
def create_fake_user(user_id: int = 1, username: str = "testuser", email: str = "test@test.com") -> User:
    return User(
        id=user_id,
        email=Email(email),
        username=username,
        password_hash="hashed_secret_password",
        group_id=2
    )

# ==========================================
# ТЕСТИ ДЛЯ РЕЄСТРАЦІЇ (AddUser)
# ==========================================
@pytest.mark.asyncio
@patch("src.auth.hashing.Hasher.get_password_hash") # Мокаємо хешер, щоб не витрачати час на реальне хешування
async def test_add_user_success(mock_get_password_hash):
    """Перевіряє успішну реєстрацію користувача та створення для нього порожнього кошика."""
    # Arrange
    mock_get_password_hash.return_value = "mocked_hash"
    
    mock_user_repo = AsyncMock()
    mock_cart_repo = AsyncMock()
    
    # Імітуємо, що такого юзера і email ще немає
    mock_user_repo.get_by_username.return_value = None
    mock_user_repo.get_by_email.return_value = None
    
    # Імітуємо збереження в БД
    expected_user = create_fake_user(user_id=10)
    mock_user_repo.create.return_value = expected_user
    
    handler = AddUserCommandHandler(mock_user_repo, mock_cart_repo)
    command = AddUserCommand(email="new@test.com", username="newuser", password="Password123")

    # Act
    result_id = await handler.handle(command)

    # Assert
    assert result_id == 10
    mock_user_repo.create.assert_called_once()
    mock_cart_repo.create.assert_called_once() # Перевіряємо, що кошик створюється!
    
    # Перевіряємо, що кошик створений для правильного user_id
    created_cart_arg = mock_cart_repo.create.call_args[0][0]
    assert created_cart_arg.user_id == 10
    assert len(created_cart_arg.items) == 0

@pytest.mark.asyncio
async def test_add_user_throws_if_username_exists():
    """Перевіряє помилку, якщо username вже зайнятий."""
    # Arrange
    mock_user_repo = AsyncMock()
    mock_cart_repo = AsyncMock()
    
    # Імітуємо, що юзер з таким ім'ям вже є
    mock_user_repo.get_by_username.return_value = create_fake_user()
    
    handler = AddUserCommandHandler(mock_user_repo, mock_cart_repo)
    command = AddUserCommand(email="test@test.com", username="testuser", password="123")

    # Act & Assert
    with pytest.raises(UsernameAlreadyExistsError, match="User 'testuser' already exists"):
        await handler.handle(command)

@pytest.mark.asyncio
async def test_add_user_throws_if_email_exists():
    """Перевіряє помилку, якщо email вже зайнятий."""
    # Arrange
    mock_user_repo = AsyncMock()
    mock_cart_repo = AsyncMock()
    
    mock_user_repo.get_by_username.return_value = None
    # Імітуємо, що email вже є
    mock_user_repo.get_by_email.return_value = create_fake_user()
    
    handler = AddUserCommandHandler(mock_user_repo, mock_cart_repo)
    command = AddUserCommand(email="test@test.com", username="newuser", password="123")

    # Act & Assert
    with pytest.raises(EmailAlreadyExistsError, match="Email 'test@test.com' already registered"):
        await handler.handle(command)

# ==========================================
# ТЕСТИ ДЛЯ ЛОГІНУ (LoginUser)
# ==========================================
@pytest.mark.asyncio
@patch("src.auth.hashing.Hasher.verify_password")
async def test_login_user_success(mock_verify_password):
    """Перевіряє успішний логін і правильне формування DTO відповіді."""
    # Arrange
    mock_verify_password.return_value = True # Імітуємо правильний пароль
    
    mock_user_repo = AsyncMock()
    fake_user = create_fake_user(user_id=5, username="john", email="john@test.com")
    mock_user_repo.get_by_username.return_value = fake_user
    
    handler = LoginUserCommandHandler(mock_user_repo)
    command = LoginUserCommand(username="john", password="correct_password")

    # Act
    result = await handler.handle(command)

    # Assert
    assert isinstance(result, UserResponseSchema)
    assert result.id == 5
    assert result.username == "john"
    assert result.email == "john@test.com"

@pytest.mark.asyncio
async def test_login_user_throws_if_user_not_found():
    """Помилка логіну: користувача не існує."""
    # Arrange
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_username.return_value = None
    
    handler = LoginUserCommandHandler(mock_user_repo)
    command = LoginUserCommand(username="ghost", password="123")

    # Act & Assert
    with pytest.raises(CredentialsError, match="Invalid email or password"):
        await handler.handle(command)

@pytest.mark.asyncio
@patch("src.auth.hashing.Hasher.verify_password")
async def test_login_user_throws_if_password_invalid(mock_verify_password):
    """Помилка логіну: пароль не підходить."""
    # Arrange
    mock_verify_password.return_value = False # Імітуємо хибний пароль
    
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_username.return_value = create_fake_user()
    
    handler = LoginUserCommandHandler(mock_user_repo)
    command = LoginUserCommand(username="testuser", password="wrong_password")

    # Act & Assert
    with pytest.raises(CredentialsError, match="Invalid email or password"):
        await handler.handle(command)