from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database.engine import db_helper
from src.database.models import Category
from src.schemas.categories import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Category).where(Category.name == category_in.name)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категорія з такою назвою вже існує."
        )
        
    new_category = Category(**category_in.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Category).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категорію не знайдено.")
    return category

@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int, 
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категорію не знайдено.")

    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
        
    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категорію не знайдено.")
        
    try:
        await db.delete(category)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Не можна видалити категорію, до якої прив'язані товари."
        )