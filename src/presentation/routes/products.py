from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.infrastructure.engine import db_helper
from src.application.use_cases.create_product_use_case import CreateProductUseCase
from src.application.use_cases.product_use_cases import (
    GetProductUseCase,
    GetAllProductsUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
)
from src.infrastructure.repositories.product_repository import ProductRepositoryImpl
from src.domain.errors.domain_errors import (
    DomainError,
    DuplicateSkuError,
    InvalidProductError,
    ProductNotFoundError,
)
from src.schemas.products import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


async def get_product_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    """Dependency for product repository"""
    return ProductRepositoryImpl(db)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository),
):
    """Create a new product"""
    use_case = CreateProductUseCase(product_repo)

    try:
        created_product = await use_case.execute(
            name=product_in.name,
            sku=product_in.sku,
            price=float(product_in.price),
            category_id=product_in.category_id,
        )

        return ProductResponse(
            id=created_product.id,
            name=created_product.name,
            sku=created_product.sku.value,
            price=float(created_product.price.amount),
            category_id=created_product.category_id,
        )

    except DuplicateSkuError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidProductError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository),
):
    """Get all products"""
    use_case = GetAllProductsUseCase(product_repo)
    products = await use_case.execute(skip=skip, limit=limit)

    return [
        ProductResponse(
            id=p.id,
            name=p.name,
            sku=p.sku.value,
            price=float(p.price.amount),
            category_id=p.category_id,
        )
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository),
):
    """Get a specific product"""
    use_case = GetProductUseCase(product_repo)

    try:
        product = await use_case.execute(product_id)
        return ProductResponse(
            id=product.id,
            name=product.name,
            sku=product.sku.value,
            price=float(product.price.amount),
            category_id=product.category_id,
        )
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository),
):
    """Update a product"""
    use_case = UpdateProductUseCase(product_repo)

    try:
        updated = await use_case.execute(
            product_id=product_id,
            name=product_update.name,
            sku=product_update.sku,
            price=float(product_update.price) if product_update.price else None,
            category_id=product_update.category_id,
        )

        return ProductResponse(
            id=updated.id,
            name=updated.name,
            sku=updated.sku.value,
            price=float(updated.price.amount),
            category_id=updated.category_id,
        )

    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateSkuError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository),
):
    """Delete a product"""
    use_case = DeleteProductUseCase(product_repo)

    try:
        await use_case.execute(product_id)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
