from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    for barrel in barrels_delivered:
        if barrel.potion_type == [0, 1, 0, 0]:
            quantity = barrel.ml_per_barrel
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))
        elif barrel.potion_type == [1, 0, 0, 0]:
            quantity = barrel.quantity
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))
        elif barrel.potion_type == [0, 0, 1, 0]:
            quantity = barrel.quantity
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))

    return "OK"

def get_value(barrel: Barrel):
    return (barrel.ml_per_barrel / barrel.price)

def get_best_value_barrel(wholesale_catalog: list[Barrel]):
    best_value = wholesale_catalog[0]
    for barrel in wholesale_catalog:
        if get_value(barrel) > get_value(best_value):
            best_value = barrel
    return best_value

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_green_potions = row1[0]
                num_red_potions = row1[3]
                num_blue_potions = row1[4]
                num_gold = row1[2]
    print(f"wholesale catalog: {wholesale_catalog}")
    best_barrel = get_best_value_barrel(wholesale_catalog)
    if best_barrel.potion_type == [0, 1, 0, 0]:
        if num_green_potions < 10 and num_gold >= best_barrel.price:
            print(f"want to buy a green barrel: {best_barrel.sku}")
            return [
                {
                    "sku": best_barrel.sku,
                    "quantity": 1
                }
            ]   
    if best_barrel.potion_type == [1, 0, 0, 0]:
        if num_red_potions < 10 and num_gold >= best_barrel.price:
            print(f"want to buy a red barrel: {best_barrel.sku}")
            return [
                {
                    "sku": best_barrel.sku,
                    "quantity": 1
                }
            ]   
    if best_barrel.potion_type == [0, 0, 1, 0]:
        if num_blue_potions < 10 and num_gold >= best_barrel.price:
            print(f"want to buy a blue barrel: {best_barrel.sku}")
            return [
                {
                    "sku": best_barrel.sku,
                    "quantity": 1
                }
            ]   
    return []
