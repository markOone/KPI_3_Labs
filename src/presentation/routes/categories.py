from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.database.engine import db_helper
from src.infrastructure.database.models import CategoryModel
from src.schemas.categories import CategoryCreate, CategoryUpdate, CategoryResponse
from sqlalchemy import select

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category_in: CategoryCreate, db: AsyncSession = Depends(db_helper.get_db_session)):
    query = select(CategoryModel).where(CategoryModel.name == category_in.name)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Категорія з такою назвою вже існує.")
    new_category = CategoryModel(**category_in.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(db_helper.get_db_session)):
    query = select(CategoryModel).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(db_helper.get_db_session)):
    query = select(CategoryModel).where(CategoryModel.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Категорію не знайдено.")
    return category