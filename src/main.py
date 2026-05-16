import logging
from typing import Union

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.database.engine import db_helper
from fastapi import Depends, HTTPException

# New presentation layer routes
from src.presentation.routes import products

app = FastAPI(
    title="E-commerce API", description="API для E-commerce проєкту", version="1.0.0"
)

# Include new presentation routes
app.include_router(products.router)


@app.get("/health")
def read_root():
    return {"Hello": "World"}


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
