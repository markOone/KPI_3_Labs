from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database.engine import db_helper
from src.application.commands.product_commands import (
    CreateProductCommand, UpdateProductCommand, DeleteProductCommand
)
from src.application.commands.product_command_handlers import (
    CreateProductCommandHandler, UpdateProductCommandHandler, DeleteProductCommandHandler
)
from src.application.queries.product_queries import GetProductQuery, GetAllProductsQuery
from src.application.queries.product_queries_handlers import (
    GetProductQueryHandler, GetAllProductsQueryHandler
)
from src.infrastructure.repositories.product_repository import ProductRepositoryImpl
from src.domain.errors.domain_errors import (
    DomainError, DuplicateSkuError, InvalidProductError, ProductNotFoundError
)
from src.schemas.products import ProductCreate, ProductUpdate, ProductResponse


router = APIRouter(prefix="/products", tags=["Products"])


async def get_product_repository(db: AsyncSession = Depends(db_helper.get_db_session)):
    """Dependency for product repository"""
    return ProductRepositoryImpl(db)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository)
):
    """Create a new product"""
    handler = CreateProductCommandHandler(product_repo)

    try:
        command = CreateProductCommand(
            name=product_in.name,
            sku=product_in.sku,
            price=float(product_in.price),
            category_id=product_in.category_id
        )
        product_id = await handler.handle(command)
        product = await product_repo.get_by_id(product_id)

        return ProductResponse(
            id=product.id,
            name=product.name,
            sku=product.sku.value,
            price=float(product.price.amount),
            category_id=product.category_id
        )

    except DuplicateSkuError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except InvalidProductError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository)
):
    """Get all products"""
    handler = GetAllProductsQueryHandler(product_repo)
    query = GetAllProductsQuery(skip=skip, limit=limit)
    return await handler.handle(query)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository)
):
    """Get a specific product"""
    handler = GetProductQueryHandler(product_repo)
    query = GetProductQuery(product_id=product_id)

    try:
        return await handler.handle(query)
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository)
):
    """Update a product"""
    handler = UpdateProductCommandHandler(product_repo)
    command = UpdateProductCommand(
        product_id=product_id,
        name=product_update.name,
        sku=product_update.sku,
        price=float(product_update.price) if product_update.price else None,
        category_id=product_update.category_id
    )

    try:
        await handler.handle(command)
        product = await product_repo.get_by_id(product_id)

        return ProductResponse(
            id=product.id,
            name=product.name,
            sku=product.sku.value,
            price=float(product.price.amount),
            category_id=product.category_id
        )

    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateSkuError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    product_repo: ProductRepositoryImpl = Depends(get_product_repository)
):
    """Delete a product"""
    handler = DeleteProductCommandHandler(product_repo)
    command = DeleteProductCommand(product_id=product_id)

    try:
        await handler.handle(command)
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
