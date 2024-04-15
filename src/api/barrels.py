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
        if barrel.potion_type == [0, 100, 0, 0]:
            quantity = barrel.quantity
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))
        elif barrel.potion_type == [100, 0, 0, 0]:
            quantity = barrel.quantity
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))
        elif barrel.potion_type == [0, 0, 100, 0]:
            quantity = barrel.quantity
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(f"wholesale catalog: {wholesale_catalog}")
    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 100, 0, 0]:
            with db.engine.begin() as connection:
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_green_potions = row1[0]
                num_gold = row1[2]
                cur.close()
            if num_green_potions < 10 and num_gold >= barrel.price:
                print(f"want to buy a green barrel: {barrel.sku}")
                return [
                    {
                        "sku": barrel.sku,
                        "quantity": 1
                    }
                ]   
        if barrel.potion_type == [100, 0, 0, 0]:
            with db.engine.begin() as connection:
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_red_potions = row1[3]
                num_gold = row1[2]
                cur.close()
            if num_red_potions < 10 and num_gold >= barrel.price:
                print(f"want to buy a red barrel: {barrel.sku}")
                return [
                    {
                        "sku": barrel.sku,
                        "quantity": 1
                    }
                ]   
        if barrel.potion_type == [0, 0, 100, 0]:
            with db.engine.begin() as connection:
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_blue_potions = row1[4]
                num_gold = row1[2]
                cur.close()
            if num_blue_potions < 10 and num_gold >= barrel.price:
                print(f"want to buy a blue barrel: {barrel.sku}")
                return [
                    {
                        "sku": barrel.sku,
                        "quantity": 1
                    }
                ]   
            
    return []
