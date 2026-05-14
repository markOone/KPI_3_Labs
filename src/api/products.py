from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database.engine import db_helper
from src.database.models import Product
from src.schemas.products import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Product).where(Product.sku == product_in.sku)
    result = await db.execute(query)
    existing_product = result.scalar_one_or_none()
    
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Товар з таким артикулом (SKU) вже існує."
        )
    
    new_product = Product(**product_in.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    return new_product


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Product).offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не знайдено."
        )
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, 
    product_update: ProductUpdate,
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не знайдено."
        )
        
    if product_update.sku is not None and product_update.sku != product.sku:
        sku_check = await db.execute(select(Product).where(Product.sku == product_update.sku))
        if sku_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Цей артикул (SKU) вже використовується іншим товаром."
            )

    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
        
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int, 
    db: AsyncSession = Depends(db_helper.get_db_session)
):
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не знайдено."
        )
        
    await db.delete(product)
    await db.commit()
    return None