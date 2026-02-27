from fastapi import APIRouter
from services.inventory_service import read_inventory, add_product

router = APIRouter(prefix="/api", tags=["inventory"])

@router.get("/inventory")
def get_inventory():
    return read_inventory()

@router.post("/inventory")
def create_product(product: dict):
    return add_product(product)