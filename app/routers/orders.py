
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.order import Order
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import Literal
from app.core.permissions import require_permission

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)
class UpdateOrderStatus(BaseModel):
    status: Literal[
        "confirmed",
        "processing",
        "shipped",
        "delivered",
        "cancelled"
    ]

@router.get("/my-orders")
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only customers can view their orders
    if not current_user.role or current_user.role.name.strip().lower() != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can view their orders"
        )

    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return {
        "message": "Orders fetched successfully",
        "total_orders": len(orders),
        "orders": [
            {
                "order_id": order.id,
                "total_amount": order.total_amount,
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at
            }
            for order in orders
        ]
    }


@router.patch("/admin/{order_id}/status")
def update_order_status(
    order_id: int,
    data: UpdateOrderStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("order_update"))
):
    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order.status = data.status

    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "status": order.status
    }

@router.get("/admin")
def get_all_orders( db: Session = Depends(get_db), current_user: User = Depends(require_permission("order_read"))
):
    orders = ( db.query(Order).order_by(Order.created_at.desc()) .all()
    )

    return {
        "message": "Orders fetched successfully",
        "total_orders": len(orders),
        "orders": [
            {
                "order_id": order.id,
                "customer": {
                    "user_id": order.user.id,
                    "first_name": order.user.first_name,
                    "last_name": order.user.last_name,
                    "email": order.user.email
                },
                "total_amount": order.total_amount,
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at
            }
            for order in orders
        ]
    }
