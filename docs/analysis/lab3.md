# Аналіз Lab 3: Command Query Separation (CQS)

## Глобальне порівняння: Use Cases (Lab 2) vs CQS (Lab 3)

### Архітектура

**Lab 2 (Use Cases):**
```
UseCase (змішана логіка)
├── Читає дані з БД
├── Змінює стан
├── Повертає результат
└── Вся логіка в одному місці
```

**Lab 3 (CQS):**
```
Command (змінює)           Query (читає)
├── DTO (immutable)        ├── DTO (immutable)
├── Handler                ├── Handler
└── Тільки запис           └── Тільки читання
```

---

## Переваги CQS (що покращилося)

### 1. **Явна семантика** ✅
Ясно видно що робить код:
- **Commands** — завжди змінюють стан
- **Queries** — завжди читають, не впливають на дані

```python
# CQS — ясно що робить
await CreateProductCommandHandler(repo).handle(command)  # ← Змінює
product = await GetProductQueryHandler(repo).handle(query)  # ← Читає

# Use Cases — не ясно
await create_product_use_case.execute(...)  # ← Що буває?
```

### 2. **Immutable DTOs** ✅
Команди не можна змінити:
```python
class CreateProductCommand(BaseModel):
    model_config = ConfigDict(frozen=True)  # ← Гарантує immutability
```

У Use Cases не було цього, можна було цільно змінити параметри.

### 3. **Розділення відповідальності** ✅
Query Handlers оптимізовані тільки для читання:
```python
class GetAllProductsQueryHandler:
    async def handle(self, query: GetAllProductsQuery) -> List[ProductResponse]:
        # Лише читання, можна оптимізувати кеш/індекси
        products = await self.product_repository.get_all(skip=query.skip)
        return [ProductResponse(...) for p in products]
```

### 4. **Масштабування** ✅
Легко оптимізувати окремо:
- **Commands** → додати транзакції
- **Queries** → додати кеш

### 5. **Тестування** ✅
Можна тестувати стан та читання окремо:
```python
# Unit-тест команди — мокаємо репозиторій
async def test_create_product_command():
    mock_repo = AsyncMock()
    handler = CreateProductCommandHandler(mock_repo)
    await handler.handle(CreateProductCommand(...))
    mock_repo.create.assert_called_once()

# Unit-тест запиту — мокаємо дані
async def test_get_product_query():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = Product(...)
    handler = GetProductQueryHandler(mock_repo)
    result = await handler.handle(GetProductQuery(...))
    assert result.name == "Test"
```

---

## Недоліки CQS (що стало складніше)

### 1. **Більше кода** ❌
Для одної сутності треба більше файлів:

**Lab 2:**
```
use_cases/
  └── product_use_cases.py  (200 lines)
```

**Lab 3:**
```
commands/
  ├── product_commands.py           (20 lines)
  └── product_command_handlers.py   (60 lines)
queries/
  ├── product_queries.py            (10 lines)
  └── product_queries_handlers.py   (40 lines)
```

Чотири файли замість одного = більше boilerplate.

### 2. **Дублювання логіки** ❌
Read Models (`ProductResponse`) повторюють поля доменної моделі:

```python
# Доменна модель
class Product(Entity):
    id: int
    name: str
    sku: Sku
    price: Money
    category_id: int

# Read Model — теж саме
class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    price: float
    category_id: int
```

При додаванні поля треба змінити в двох місцях.

### 3. **Складність контролерів** ❌
Контролер тепер робить два запити (Command + Query):

```python
@router.post("/")
async def create_product(product_in: ProductCreate, repo: ProductRepository):
    # 1. Команда
    product_id = await CreateProductCommandHandler(repo).handle(command)
    
    # 2. Запит (додатковий)
    product = await GetProductQueryHandler(repo).handle(GetProductQuery(product_id=product_id))
    
    return product  
```

Результат: **+1 SQL запит на будь-яку зміну** (SELECT після INSERT/UPDATE).

### 4. **Складніші тести** ❌
Тести для контролера тепер потребує мокування і Команди, і Запиту:

```python
# Раніше (Use Cases)
async def test_create_product():
    result = await use_case.execute(...)  # 1 мок

# Тепер (CQS)
async def test_create_product():
    await command_handler.handle(...)  # 1 мок
    result = await query_handler.handle(...)  # 2 мок
```

## Порівняльна таблиця

| Критерій | Lab 2 (Use Cases) | Lab 3 (CQS) | Переможець |
|----------|-------------------|-----------|-----------|
| **Файлів на сутність** | 1 | 4 | Lab 2 |
| **Ясність намірів** | ⚠️ Змішано | ✅ Явно | Lab 3 |
| **Boilerplate** | 200 lines | 130 lines × 2 = 260 lines | Lab 2 |
| **SQL запитів на зміну** | 1 | 2 (Command + Query) | Lab 2 |
| **Immutable DTOs** | ❌ Ні | ✅ Так | Lab 3 |
| **Легко тестувати** | ⚠️ Складно | ✅ Просто | Lab 3 |
| **Масштабуваність** | ⚠️ Обмежена | ✅ Велика | Lab 3 |
| **Складність** | ⚠️ Середня | ❌ Висока | Lab 2 |

---

## Коли CQS має сенс?

### ✅ Використовувати CQS, якщо:
1. **Читання і запис мають різні темпи** — мало оновлень, багато читання
2. **Потреба в кешуванні** — Queries можна кешувати, Commands ні
3. **Окремі сховища** — read DB відрізняється від write DB
4. **Масштабування** — різні оптимізації для читання/запису
5. **Складна бізнес-логіка** — велика кількість операцій

### ❌ Використовувати Use Cases, якщо:
1. **Прості CRUD операції** — однакові темпи читання/запису
2. **Мало сутностей** — 5-10 таблиць
3. **Малий проект** — один розробник
4. **Жорсткі дедлайни** — немає часу на boilerplate
5. **Одна БД** — немає плану на масштабування

---