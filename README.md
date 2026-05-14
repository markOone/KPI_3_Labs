# KPI_3_Labs


## 1. Підготовка оточення
```
# Створення папки оточення
python -m venv venv

# Активація (Windows)
source venv\Scripts\activate

# Встановлення необхідних пакетів
pip install -r requirements.txt
```


## 2. Запуск через Docker
```
# Зібрати образи та запустити всі сервіси
docker-compose up --build
```