import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.database.engine import db_helper

from src.presentation.routes import products, auth, cart, categories, orders, stocks

app = FastAPI(
    title="E-commerce API", 
    description="API для E-commerce проєкту (Clean Layered Architecture)", 
    version="2.0.0"
)

app.include_router(products.router)
app.include_router(auth.router)
app.include_router(cart.router)
app.include_router(categories.router)
app.include_router(orders.router)
app.include_router(stocks.router)

@app.get("/health")
def read_root():
    return {"status": "healthy", "architecture": "layered"}

@app.get("/health/database")
async def check_database_health(db: AsyncSession = Depends(db_helper.get_db_session)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "online"}
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=500, detail="Database is offline or unresponsive"
        )