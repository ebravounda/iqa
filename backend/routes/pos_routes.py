from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional, List
import uuid
import logging

from database import db
from auth import get_current_admin, check_role, check_permission
from models import ProductCreate, ProductUpdate, SaleCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

async def check_pos_access(gym_id: str):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    plan_id = gym.get("saas_plan_id")
    if plan_id:
        plan = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
        if plan and not plan.get("has_pos", False):
            raise HTTPException(status_code=403, detail="El plan SaaS de este gimnasio no incluye TPV/POS. Actualice su plan.")
    return gym

# ==================== PRODUCTS ====================

@router.post("/pos/products")
async def create_product(product: ProductCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    check_permission(admin, "pos_products")
    await check_pos_access(product.gym_id)
    product_dict = product.model_dump()
    product_dict["id"] = str(uuid.uuid4())
    product_dict["active"] = True
    product_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.pos_products.insert_one(product_dict)
    product_dict.pop("_id", None)
    return product_dict

@router.get("/pos/products")
async def get_products(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"active": True}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    products = await db.pos_products.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return products

@router.put("/pos/products/{product_id}")
async def update_product(product_id: str, product_update: ProductUpdate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    update_data = {k: v for k, v in product_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.pos_products.update_one({"id": product_id}, {"$set": update_data})
    product = await db.pos_products.find_one({"id": product_id}, {"_id": 0})
    return product

@router.delete("/pos/products/{product_id}")
async def delete_product(product_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    check_permission(admin, "pos_products")
    await db.pos_products.update_one({"id": product_id}, {"$set": {"active": False}})
    return {"message": "Producto eliminado"}

# ==================== SALES ====================

@router.post("/pos/sales")
async def create_sale(sale: SaleCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    check_permission(admin, "pos_sell")
    await check_pos_access(sale.gym_id)
    
    items_detail = []
    total = 0
    for item in sale.items:
        product = await db.pos_products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado")
        if product.get("stock", 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{product['name']}'. Disponible: {product.get('stock', 0)}")
        line_total = item.unit_price * item.quantity
        total += line_total
        items_detail.append({
            "product_id": item.product_id,
            "product_name": product["name"],
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "cost_price": product.get("cost_price", 0),
            "line_total": line_total
        })
        # Decrease stock
        await db.pos_products.update_one(
            {"id": item.product_id},
            {"$inc": {"stock": -item.quantity}}
        )
    
    gym = await db.gyms.find_one({"id": sale.gym_id}, {"_id": 0})
    currency = (gym or {}).get("currency", "EUR")
    
    sale_dict = {
        "id": str(uuid.uuid4()),
        "gym_id": sale.gym_id,
        "items": items_detail,
        "total": total,
        "currency": currency,
        "payment_method": sale.payment_method,
        "member_id": sale.member_id,
        "notes": sale.notes,
        "registered_by": admin["id"],
        "registered_by_name": admin.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.pos_sales.insert_one(sale_dict)
    sale_dict.pop("_id", None)
    return sale_dict

@router.get("/pos/sales")
async def get_sales(
    gym_id: Optional[str] = None, date_from: Optional[str] = None,
    date_to: Optional[str] = None, admin: dict = Depends(get_current_admin)
):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    sales = await db.pos_sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return sales

@router.get("/pos/sales/{sale_id}")
async def get_sale(sale_id: str, admin: dict = Depends(get_current_admin)):
    sale = await db.pos_sales.find_one({"id": sale_id}, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return sale

@router.get("/pos/stats")
async def get_pos_stats(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = {**query, "created_at": {"$gte": today_start.isoformat()}}
    today_sales = await db.pos_sales.find(today_query, {"_id": 0}).to_list(1000)
    today_total = sum(s.get("total", 0) for s in today_sales)
    
    month_start = today_start.replace(day=1)
    month_query = {**query, "created_at": {"$gte": month_start.isoformat()}}
    month_sales = await db.pos_sales.find(month_query, {"_id": 0}).to_list(5000)
    month_total = sum(s.get("total", 0) for s in month_sales)
    
    # Low stock products
    stock_query = {"active": True, "stock": {"$lte": 5}}
    if admin["role"] != "super_admin":
        stock_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        stock_query["gym_id"] = gym_id
    low_stock = await db.pos_products.find(stock_query, {"_id": 0}).to_list(50)
    
    # Count total products
    product_count_query = {"active": True}
    if admin["role"] != "super_admin":
        product_count_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        product_count_query["gym_id"] = gym_id
    total_products = await db.pos_products.count_documents(product_count_query)
    
    return {
        "today_sales": len(today_sales),
        "today_total": today_total,
        "today_revenue": today_total,
        "month_sales": len(month_sales),
        "month_total": month_total,
        "month_revenue": month_total,
        "total_products": total_products,
        "low_stock_products": low_stock
    }


@router.get("/pos/categories")
async def get_pos_categories(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get distinct product categories for a gym"""
    query = {"active": True}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    categories = await db.pos_products.distinct("category", query)
    # Filter out None/empty and add default
    cats = [c for c in categories if c]
    if not cats:
        cats = ["general"]
    return sorted(cats)


@router.delete("/pos/categories/{category_name}")
async def delete_category(category_name: str, gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    check_permission(admin, "pos_products")
    query = {"category": category_name, "active": True}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    result = await db.pos_products.update_many(query, {"$set": {"category": "General"}})
    return {"message": f"Categoria eliminada. {result.modified_count} productos movidos a General"}
