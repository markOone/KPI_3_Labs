from typing import List
from src.application.queries.order_queries import GetOrderQuery, GetUserOrdersQuery
from src.domain.repositories.repositories import OrderRepository
from src.domain.errors.domain_errors import OrderNotFoundError
from src.schemas.orders import OrderResponse, OrderItemOut

class GetOrderQueryHandler:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def handle(self, query: GetOrderQuery) -> OrderResponse:
        order = await self.order_repository.get_by_id(query.order_id)
        if not order:
            raise OrderNotFoundError(f"Order {query.order_id} not found")
        
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_price=order.total_price.amount,
            created_at=order.created_at,
            items=[
                OrderItemOut(
                    product_id=i.product_id, 
                    quantity=i.quantity.value, 
                    price=i.price_at_purchase.amount
                ) for i in order.items
            ]
        )

class GetUserOrdersQueryHandler:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def handle(self, query: GetUserOrdersQuery) -> List[OrderResponse]:
        orders = await self.order_repository.get_by_user_id(query.user_id)
        return [
            OrderResponse(
                id=o.id,
                user_id=o.user_id,
                status=o.status,
                total_price=o.total_price.amount,
                created_at=o.created_at,
                items=[
                    OrderItemOut(
                        product_id=i.product_id, 
                        quantity=i.quantity.value, 
                        price=i.price_at_purchase.amount
                    ) for i in o.items
                ]
            ) for o in orders
        ]