
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.cart import Cart
from app.models.cart_item import CartItems
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItems
from app.core.security import get_current_user

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def checkout(db: Session = Depends(get_db),current_user=Depends(get_current_user)):

    if not current_user.role or current_user.role.name.strip().lower() != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can place orders"
        )

    try:
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).with_for_update().first()

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        cart_items = db.query(CartItems).filter(CartItems.cart_id == cart.id).all()

        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your cart is empty"
            )

        total_amount = Decimal("0.00")
        order_items = []

        for cart_item in cart_items:
            product = db.query(Product).filter(Product.id == cart_item.product_id,Product.is_active == True ).with_for_update().first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {cart_item.product_id} is not available"
                )

            if product.stock < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product.name}"
                )

            price = Decimal(str(product.price))
            subtotal = price * cart_item.quantity

            total_amount += subtotal

            order_items.append({
                "product": product,
                "quantity": cart_item.quantity,
                "price": price,
                "subtotal": subtotal
            })

        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            status="pending",
            payment_status="pending"
        )

        db.add(order)
        db.flush()

        for item in order_items:
            db.add(
                OrderItems(
                    order_id=order.id,
                    product_id=item["product"].id,
                    quantity=item["quantity"],
                    price=item["price"],
                    subtotal=item["subtotal"]
                )
            )

            item["product"].stock -= item["quantity"]

        db.query(CartItems).filter(
            CartItems.cart_id == cart.id
        ).delete(synchronize_session=False)

        db.commit()
        db.refresh(order)

        return {
            "message": "Order placed successfully",
            "order_id": order.id,
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_status": order.payment_status
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to place order"
        )
