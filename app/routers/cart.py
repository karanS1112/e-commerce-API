
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.cart import Cart
from app.models.cart_item import CartItems
from app.models.product import Product
from decimal import Decimal

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


class AddToCartRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

class UpdateCartRequest(BaseModel):
    quantity: int = Field(ge=0)


@router.post("/add", status_code=status.HTTP_200_OK)
def add_to_cart(request: AddToCartRequest,db: Session = Depends(get_db),current_user=Depends(get_current_user)):
    try:
        # check if the current user is a customer
        if not current_user.role or current_user.role.name.strip().lower() != "customer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers can add products to cart"
            )

        #Check product
        product = db.query(Product).filter(Product.id == request.product_id,Product.is_active == True).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or inactive"
            )

        # Check stock
        if product.stock < request.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient product stock"
            )
        
    

        #  Get customer's cart
        cart = db.query(Cart).filter(
            Cart.user_id == current_user.id
        ).first()

        #  Create cart if it does not exist
        if not cart:
            cart = Cart(user_id=current_user.id)
            db.add(cart)
            db.flush()

        # Check whether product already exists in cart
        cart_item = db.query(CartItems).filter(
            CartItems.cart_id == cart.id,
            CartItems.product_id == product.id
        ).first()

        if cart_item:
            new_quantity = cart_item.quantity + request.quantity

            #  Check total requested quantity against stock
            if new_quantity > product.stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Requested quantity exceeds available stock"
                )

            cart_item.quantity = new_quantity

        else:
            #  Add new product to cart
            cart_item = CartItems(
                cart_id=cart.id,
                product_id=product.id,
                quantity=request.quantity
            )

            db.add(cart_item)

        db.commit()
        db.refresh(cart_item)

        return {
            "message": "Product added to cart successfully",
            "data": {
                "cart_id": cart.id,
                "item_id": cart_item.id,
                "product_id": product.id,
                "product_name": product.name,
                "price": float(product.price),
                "quantity": cart_item.quantity,
                "subtotal": float(product.price * cart_item.quantity)
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


@router.get("/")
def get_cart(db: Session = Depends(get_db),current_user=Depends(get_current_user)):
    # Check customer role
    if not current_user.role or current_user.role.name.strip().lower() != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can view their cart"
        )

    # Get customer's cart
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        return {
            "message": "Your cart is empty",
            "data": {
                "cart_id": None,
                "items": [],
                "total_items": 0,
                "grand_total": 0.0
            }
        }

    # Get cart items
    cart_items = db.query(CartItems).filter(
        CartItems.cart_id == cart.id
    ).all()

    items = []
    grand_total = Decimal("0.00")
    total_items = 0

    for item in cart_items:
        product = item.product

        # Skip inactive products
        if not product or not product.is_active:
            continue

        price = Decimal(str(product.price))
        subtotal = price * item.quantity

        grand_total += subtotal
        total_items += item.quantity

        items.append({
            "item_id": item.id,
            "product_id": product.id,
            "product_name": product.name,
            "price": float(price),
            "quantity": item.quantity,
            "subtotal": float(subtotal)
        })

    return {
        "message": "Cart retrieved successfully",
        "data": {
            "cart_id": cart.id,
            "items": items,
            "total_items": total_items,
            "grand_total": float(grand_total)
        }
    }

@router.put("/update/{item_id}")
def update_cart_item( item_id: int,request: UpdateCartRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    # Check customer role
    if not current_user.role or current_user.role.name.strip().lower() != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can update their cart"
        )

        # Find customer's cart
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    # Find item inside customer's cart
    cart_item = db.query(CartItems).filter(
        CartItems.id == item_id,
        CartItems.cart_id == cart.id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    # Check product
    product = db.query(Product).filter(
        Product.id == cart_item.product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )
    
    # If quantity is set to 0, remove the item from the cart
    if request.quantity == 0:
        db.delete(cart_item)
        db.commit()

        return {
            "message": "Product removed from cart successfully"
        }
    
    # Check stock
    if request.quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock"
        )

    # Update quantity
    cart_item.quantity = request.quantity

    db.commit()
    db.refresh(cart_item)

    subtotal = Decimal(str(product.price)) * cart_item.quantity

    return {
        "message": "Cart quantity updated successfully",
        "data": {
            "item_id": cart_item.id,
            "product_id": product.id,
            "product_name": product.name,
            "price": float(product.price),
            "quantity": cart_item.quantity,
            "subtotal": float(subtotal)
        }
    }

@router.delete("/remove/{item_id}")
def remove_cart_item(item_id: int,db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        # Check customer role
        if not current_user.role or current_user.role.name.strip().lower() != "customer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers can remove products from cart"
            )

        # Get customer's cart
        cart = db.query(Cart).filter(
            Cart.user_id == current_user.id
        ).first()

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        # Find item inside customer's cart
        cart_item = db.query(CartItems).filter(
            CartItems.id == item_id,
            CartItems.cart_id == cart.id
        ).first()

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )

        # Remove item
        db.delete(cart_item)
        db.commit()

        return {
            "message": "Product removed from cart successfully",
            "data": {
                "item_id": item_id
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

@router.delete("/clear")
def clear_cart(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        # Check customer role
        if  not current_user.role or current_user.role.name.strip().lower() != "customer":
        
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers can clear their cart"
            )

        # Get customer's cart
        cart = db.query(Cart).filter(
            Cart.user_id == current_user.id
        ).first()

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        # Delete all cart items
        deleted_items = db.query(CartItems).filter(
            CartItems.cart_id == cart.id
        ).delete(synchronize_session=False)

        db.commit()

        return {
            "message": "Cart cleared successfully",
            "data": {
                "cart_id": cart.id,
                "deleted_items": deleted_items
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise