from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        row1 = cur.fetchone()
        gold = row1[1]
        green_ml = row1[0]
        red_ml = row1[2]
        blue_ml = row1[3]
        dark_ml = row1[4]
        cur = connection.execute(sqlalchemy.text("SELECT potions.inventory FROM potions;"))
        potions = cur.fetchall()
        
    total = 0
    for inventory in potions:
        total += inventory[0]
    
    return {"number_of_potions": total, "ml_in_barrels": (green_ml + red_ml + blue_ml + dark_ml), "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        row1 = cur.fetchone()
        gold = row1[1]
    
    potion_capacity = 0
    ml_capacity = 0
    
    if gold >= 2000 and (get_total_potions_in_inventory() >= 45) and (get_total_ml_in_inventory() >= 8000):
        potion_capacity += 1
        ml_capacity += 1
        print("Want to buy 1 more ml_capacity and 1 more potion_capacity")
    elif gold >= 1000 and (get_total_potions_in_inventory() >= 45):
        potion_capacity += 1
        print("Want to buy 1 more potion_capacity")
    elif gold >= 1000 and (get_total_ml_in_inventory() >= 8000):
        ml_capacity += 1
        print("Want to buy 1 more ml_capacity")

    return {
        "potion_capacity": potion_capacity,
        "ml_capacity": ml_capacity
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

def get_total_ml_in_inventory():
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        row1 = cur.fetchone()
        green_ml = row1[0]
        red_ml = row1[2]
        blue_ml = row1[3]
        dark_ml = row1[4]
    return (green_ml + red_ml + blue_ml + dark_ml)

def get_total_potions_in_inventory():
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT potions.inventory FROM potions;"))
        potions = cur.fetchall()
        
    total = 0
    for inventory in potions:
        total += inventory[0]
    
    return total

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        if capacity_purchase.ml_capacity > 0:
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = (global_inventory.gold - " + str(1000 * capacity_purchase.ml_capacity) + ");"))
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET ml_capacity = (global_inventory.ml_capacity + " + str(capacity_purchase.ml_capacity) + ");"))
        if capacity_purchase.potion_capacity > 0:
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = (global_inventory.gold - " + str(1000 * capacity_purchase.potion_capacity) + ");"))
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET potion_capacity = (global_inventory.potion_capacity + " + str(capacity_purchase.potion_capacity) + ");"))

    return "OK"
