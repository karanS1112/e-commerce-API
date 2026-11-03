
from typing import Optional
from pathlib import Path
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.permissions import require_permission
from app.models.product import Product
from app.models.product_image import ProductImage
from app.core.config import settings


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

UPLOAD_DIR = Path(settings.PRODUCT_UPLOAD_DIR)

ALLOWED_EXTENSIONS = {
    extension.strip().lower()
    for extension in settings.PRODUCT_ALLOWED_EXTENSIONS.split(",")
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)



@router.post("/")
def create_product(
    product_name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(0),
    images:list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("product_create"))
):
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0"
        )

    if stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock cannot be negative"
        )

    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one product image is required"
        )

    product = Product(
        name=product_name,
        description=description,
        price=price,
        stock=stock,
        is_active=True
    )

    db.add(product)
    db.flush()

    for index, image in enumerate(images):
        extension = Path(image.filename or "").suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format: {extension}"
            )

        filename = f"{uuid.uuid4().hex}{extension}"
        file_path = UPLOAD_DIR / filename

        with file_path.open("wb") as file:
            shutil.copyfileobj(image.file, file)

        db.add(ProductImage(
            product_id=product.id,
            image_url=f"/uploads/products/{filename}",
            is_primary=(index == 0)
        ))

    db.commit()
    db.refresh(product)

    return {
        "message": "Product created successfully",
        "data": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "stock": product.stock,
            "is_active": product.is_active,
            "images": [
                {
                    "id": image.id,
                    "image_url": image.image_url,
                    "is_primary": image.is_primary
                }
                for image in product.images
            ]
        }
    }

@router.get("/")
def get_products( skip: int = 0,limit: int = 10,db: Session = Depends(get_db), current_user=Depends(require_permission("product_read"))):
    products = db.query(Product).offset(skip).limit(limit).all()
    return {
        "message": "Products retrieved successfully",
        "data": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": float(product.price),
                "stock": product.stock,
                "is_active": product.is_active,
                "images": [
                    {
                        "id": image.id,
                        "image_url": image.image_url,
                        "is_primary": image.is_primary
                    }
                    for image in product.images
                ]
            }
            for product in products
        ]
    }

@router.put("/{product_id}")
def update_product(
    product_id: int,
    product_name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(0),
    images: Optional[list[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("product_update"))
):
    # Find product
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Validate price and stock
    if price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than 0"
        )

    if stock < 0:
        raise HTTPException(
            status_code=400,
            detail="Stock cannot be negative"
        )

    # Update product details
    product.name = product_name
    product.description = description
    product.price = price
    product.stock = stock

    # Upload new images if provided
    if images:
        for index, image in enumerate(images):
            extension = Path(image.filename or "").suffix.lower()

            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image format: {extension}"
                )

            filename = f"{uuid.uuid4().hex}{extension}"
            file_path = UPLOAD_DIR / filename

            with file_path.open("wb") as file:
                shutil.copyfileobj(image.file, file)

            db.add(
                ProductImage(
                    product_id=product.id,
                    image_url=f"/uploads/products/{filename}",
                    is_primary=(index == 0)
                )
            )

    db.commit()
    db.refresh(product)

    return {
        "message": "Product updated successfully",
        "data": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "stock": product.stock,
            "is_active": product.is_active,
            "images": [
                {
                    "id": image.id,
                    "image_url": image.image_url,
                    "is_primary": image.is_primary
                }
                for image in product.images
            ]
        }
    }



@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("product_delete"))
):
    # Find product
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Delete product image records
    db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).delete(synchronize_session=False)

    # Delete product
    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }

# single product get by id
@router.get("/{product_id}")
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("product_read"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return {
        "message": "Product retrieved successfully",
        "data": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "stock": product.stock,
            "is_active": product.is_active,
            "images": [
                {
                    "id": image.id,
                    "image_url": image.image_url,
                    "is_primary": image.is_primary
                }
                for image in product.images
            ]
        }
    }
