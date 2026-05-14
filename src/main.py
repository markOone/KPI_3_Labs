import logging
from typing import Union

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.database.engine import db_helper
from fastapi import Depends, HTTPException

from src.api import products
from src.api import categories

app = FastAPI(
    title="E-commerce API",
    description="API для E-commerce проєкту",
    version="1.0.0"
)

app.include_router(products.router)
app.include_router(categories.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/health")
async def check_database_health(db: AsyncSession = Depends(db_helper.get_db_session)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "online"}
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Database is offline or unresponsive"
        )