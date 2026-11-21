from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")


class CategoryOut(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)
    size: str | None = Field(default=None, max_length=50)
    image_url: str | None = Field(default=None, max_length=255, pattern=r"^/static/uploads/[\w.-]+$")
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=1000)
    custom_text: str | None = Field(default=None, max_length=100)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    customer_email: EmailStr
    shipping_address: str = Field(min_length=5, max_length=255)
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    quantity: int
    unit_price: Decimal
    custom_text: str | None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_name: str
    customer_email: str
    shipping_address: str
    status: str
    total: Decimal
    created_at: datetime
    items: list[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "paid", "shipped", "cancelled"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
