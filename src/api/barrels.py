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
            quantity = barrel.ml_per_barrel
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))
        elif barrel.potion_type == [0, 0, 1, 0]:
            quantity = barrel.ml_per_barrel
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))

    return "OK"

def get_value(barrel: Barrel):
    return (barrel.ml_per_barrel / barrel.price)

def get_best_value_barrel(wholesale_catalog: list[Barrel]):
    if wholesale_catalog == None or len(wholesale_catalog) == 0:
        return None
    else:
        with db.engine.begin() as connection:
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_gold = row1[2]
    
        best_value = wholesale_catalog[0]
    
        for barrel in wholesale_catalog:
            if get_value(barrel) > get_value(best_value):
                best_value = barrel
        
        while (best_value and num_gold <= best_value.price):
            wholesale_catalog.remove(best_value) #remove a best barrel if i can't afford it
            best_value = get_best_value_barrel(wholesale_catalog) # find the next best barrel
    
        if (best_value and (best_value.ml_per_barrel / best_value.price)) > 2: # make sure i'm not losing money bc all my potions are 100ml and cost 50 gold
            return best_value
        else:
            get_best_value_barrel(wholesale_catalog.remove(best_value))

def what_ml_do_i_need():
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        row1 = cur.fetchone()
        num_green_ml = row1[1]
        num_red_ml = row1[5]
        num_blue_ml = row1[6]
        num_green_potions = row1[0]
        num_red_potions = row1[3]
        num_blue_potions = row1[4]
    
    total_green = num_green_ml + (num_green_potions * 100)
    total_red = num_red_ml + (num_red_potions * 100)
    total_blue = num_blue_ml + (num_blue_potions * 100)
    total_all = total_green + total_red + total_blue
    colors_needed = [total_red, total_green, total_blue]
    
    for color in colors_needed:
        if ((color / total_all) > .4):
            colors_needed.remove(color)
    
    return colors_needed
    
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
    
    if best_barrel == None:
        print("No barrels in the catalog I wouldn't lose money on when selling for 50 gold.")
        return []
    
    print(f"best barrel i can afford: {best_barrel}")

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
