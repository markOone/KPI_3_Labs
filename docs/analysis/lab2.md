# Лабораторна робота 2: Аналіз шарової архітектури та доменної моделі

## 1. Що змінилося порівняно з лаб 1

### Структура проєкту

**Лаб 1:**
```
src/
├── api/              # Маршрути + бізнес-логіка змішані
├── auth/             # Аутентифікація
├── database/         # ORM моделі
├── schemas/          # DTO для HTTP
├── config/
├── exceptions/
```

**Лаб 2 (4-шарова архітектура):**
```
src/
├── domain/           # Бізнес-логіка, не залежить від фреймворку
│   ├── entities/     # Product, User, Cart, Order
│   ├── value_objects/ # Email, Money, Quantity, Sku
│   ├── errors/       # DomainError та спеціалізовані
│   ├── repositories/ # Інтерфейси (контракти)
│   └── factories/    # Domain Factory для валідації
├── application/      # Use Cases, оркестрація
│   └── use_cases/    # CreateProduct, GetProduct, Cart операції...
├── infrastructure/   # Реалізація деталей
│   ├── database/     # ORM моделі (ProductModel, UserModel...)
│   ├── repositories/ # Реалізація інтерфейсів (ProductRepositoryImpl...)
│   └── mappers/      # Конвертація domain ↔ ORM
├── presentation/     # HTTP шар
│   └── routes/       # FastAPI маршрути
└── config/
```

### Ключові зміни

| Аспект | Лаб 1 | Лаб 2 |
|--------|-------|-------|
| Бізнес-логіка | У маршрутах (api/) | У domain entities та use cases |
| ORM моделі | Напряму у маршрутах | Окремий шар, мають "Model" суфікс |
| Валідація | В маршрутах, розсіяна | Domain Factory, централізована |
| Помилки | HTTPException | DomainError, потім мапяться на HTTP |
| Залежності | Всередину маршрутів | Через інтерфейси (DIP) |

## 2. Переваги розділення на шари

### 2.1 Тестування
- **Лаб 1:** Тести вимагали повного FastAPI сервера і бази даних
- **Лаб 2:** Unit-тести domain логіки запускаються без DB і без HTTP-сервера
  ```bash
  # Лаб 2: чистий unit тест
  pytest tests/test_domain.py -v
  # Не потребує: FastAPI, БД, Docker
  ```

### 2.2 Незалежність від інфраструктури
- **Лаб 1:** Змінити БД на іншу вимагала переписування маршрутів
- **Лаб 2:** Достатньо замінити `ProductRepositoryImpl` на нову реалізацію
  ```python
  # Domain не знає про SQL або якусь іншу реалізацію
  class ProductFactory:
      def __init__(self, repository: ProductRepository):  # Інтерфейс!
          self.repository = repository
  ```

### 2.3 Простота розширення
- **Лаб 1:** Додання нового юзкейсу часто вимагало дублювання коду
- **Лаб 2:** CreateProductUseCase, GetProductUseCase, UpdateProductUseCase — окремі класи, переиспользуются

### 2.4 Захист бізнес-правил
- **Лаб 1:** SKU унікальність перевіряється в маршруті
- **Лаб 2:** SKU унікальність перевіряється у `ProductFactory` — гарантовано захищена в усіх casos
  ```python
  # Неможливо обійти!
  existing = await self.repository.get_by_sku(sku)
  if existing:
      raise DuplicateSkuError(...)
  ```

### 2.5 Розуміння коду
- **Лаб 1:** Domain knowledge розсіяна по маршрутах
- **Лаб 2:** `Cart`, `Stock.reduce()`, `Order.can_cancel()` — явна бізнес-логіка

## 3. Недоліки та ускладнення

### 3.1 Більше коду
- Потрібні mapper класси для конвертації domain ↔ ORM
- Більше файлів та модулів
- Кожен use case — окремий файл

### 3.2 Складніша навігація
- Для розуміння "що відбувається при POST /products" треба переглянути:
  1. `presentation/routes/products.py` (маршрут)
  2. `application/use_cases/create_product_use_case.py` (use case)
  3. `domain/factories/product_factory.py` (валідація)
  4. `infrastructure/repositories/product_repository.py` (BD операція)
  5. `infrastructure/mappers/mappers.py` (конвертація)

### 3.3 Синхронізація моделей
- Domain модель та ORM модель можуть розійтися
- Mapper має бути актуальним

### 3.4 Значні зміни до розробки
- Лаб 1 була скоро розроблена (монолітний шар)
- Лаб 2 потребує планування та дизайну перед кодуванням

## 4. Наскільки простіше тепер змінити БД або фреймворк?

### Сценарій: Міграція з SQLAlchemy на MongoDB

**Лаб 1:**
```
❌ Потрібно переписати:
  - Усі маршрути (api/*.py)
  - SQL запити → MongoDB queries
  - Модельні relationships → іниціалізація
  - Схеми (schemas/*.py) можуть змінитися
```

**Лаб 2:**
```
✅ Достатньо замінити:
  1. ProductRepositoryImpl → MongoProductRepositoryImpl
     (реалізує той же інтерфейс ProductRepository)
  2. ORM моделі в infrastructure/database/ → Pydantic/dataclass моделі
  3. Mapper логіка для MongoDB документів

Domain и Application層 залишаються незмінними!
```

**Приклад:**
```python
# infrastructure/repositories/mongo_product_repository.py
class MongoProductRepositoryImpl(ProductRepository):
    def __init__(self, db):
        self.db = db  # MongoDB instance
    
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        doc = await self.db.products.find_one({"_id": product_id})
        return ProductMapper.from_mongo(doc) if doc else None
    # ...

# Domain код не змінюється!
```

### Сценарій: Міграція FastAPI → Flask

**Лаб 1:**
```
❌ Переписувати:
  - Усі @router.post/@router.get → @app.route()
  - Маршрути та їх залежності
```

**Лаб 2:**
```
✅ Замінити лише presentation/routes:
  - Нові Flask blueprints у presentation/
  - Domain, Application, Infrastructure залишаються однаковими
```

## 5. Вибір Anemic vs Rich Domain Model

### Обраний підхід: **Rich Domain Model**

**Обґрунтування:**

1. **Захист інваріантів**
   ```python
   # Rich: логіка у домену
   cart.add_item(product_id, quantity, price)  # Валідація всередині
   
   # Anemic: логіка у use case
   if quantity <= 0:
       raise ValueError(...)
   cart.items.append(...)
   ```

2. **Запобігання невалідним станам**
   ```python
   # Rich: неможливо створити невалідне значення
   stock = Stock(..., quantity=Quantity(-5))  # ValueError відразу!
   
   # Anemic: потребує зовнішньої перевірки
   stock.quantity = -5  # Ніхто не помітить!
   ```

3. **Простота тестування**
   ```python
   # Rich: тест просто — немає залежностей
   def test_cart_add_item():
       cart = Cart(...)
       cart.add_item(1, Quantity(5), Money(100))
       assert len(cart.items) == 1
   
   # Anemic: тестувати легко, але логіка розсіяна
   ```

4. **Самодокументування**
   ```python
   # Rich: код читаємо
   if order.can_cancel():  # зрозуміло!
       order.status = "cancelled"
   
   # Anemic: потрібен контекст
   if order.status == "pending":  # чому саме "pending"?
       ...
   ```

## 6. Рекомендації для подальших лаб

1. **Тестування:**
   - Unit-тести domain без DB ✅
   - Integration-тести з реальною BD
   - End-to-end тести HTTP шляхів

2. **Документація:**
   - Diagrams які показують залежності шарів
   - ADR (Architecture Decision Records) для найважливіших рішень

3. **Масштабування:**
   - Для мікросервісів: Presentation → Application зберігаються, Infrastructure міняється (внутрішні сервіси vs зовнішні API)
   - Для складних бізнес-процесів: Application вигідно розділити на сценарії та модулі

## Висновок

Лаб 2 демонструє, як правильна архітектура дає гнучкість та надійність. Ціна — більше початкового коду, але інвестиція окупається при внесенні змін та розширенні.

**Ключовий навик:** Розуміння того, що код повинен бути структурований так, щоб його **змінювалося легко**, а **помилок було мало**.
