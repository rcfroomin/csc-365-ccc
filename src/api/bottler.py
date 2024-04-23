from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

def build_inventory():
    catalog = []
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT potions.item_sku FROM potions;"))
        potion_list = cur.fetchall()
        
        for potion in potion_list:
            cur = connection.execute(sqlalchemy.text("SELECT potions.red, potions.green, potions.blue, potions.dark FROM potions WHERE potions.item_sku = '" + potion[0] + "';"))
            potion_type = cur.fetchone()
            potion_type_list = []
            for color in potion_type:
                potion_type_list.append(color)
            catalog.append([potion[0], potion_type_list])

    return catalog

def check_enough(needed: list): # needed = list[potion_sku, potion_type]
    plan = []
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        row1 = cur.fetchone()
        num_red_ml = row1[5]
        num_green_ml = row1[1]
        num_blue_ml = row1[6]
        num_dark_ml = row1[7]
    
    for potion in needed:
        enough_red = False
        enough_green = False
        enough_blue = False
        enough_dark = False
        if (potion[1][0] <= num_red_ml):
            enough_red = True
        if (potion[1][1] <= num_green_ml):
            enough_green = True
        if (potion[1][2] <= num_blue_ml):
            enough_blue = True
        if (potion[1][3] <= num_dark_ml):
            enough_dark = True
        if enough_red and enough_green and enough_blue and enough_dark:
            plan.append(
                {
                    "potion_type": potion[1],
                    "quantity": 1
                }
            )
            num_red_ml -= potion[1][0]
            num_green_ml -= potion[1][1]
            num_blue_ml -= potion[1][2]
            num_dark_ml -= potion[1][3]

    return plan

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"Potions delievered to Me: {potions_delivered} order_id: {order_id}")
    inv = build_inventory()
    for potion in potions_delivered:
        for item in inv:
            if potion.potion_type == item[1]:
                quantity = potion.quantity
                num_red_ml =item[1][0]
                num_green_ml = item[1][1]
                num_blue_ml = item[1][2]
                num_dark_ml = item[1][3]
                with db.engine.begin() as connection:
                    result = connection.execute(sqlalchemy.text("UPDATE potions SET inventory = (potions.inventory + " + str(quantity) + ") WHERE potions.item_sku = '" + item[0] + "';"))
                    result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - " + str(num_red_ml) + ";"))
                    result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - " + str(num_green_ml) + ";"))
                    result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml - " + str(num_blue_ml) + ";"))
                    result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_dark_ml = num_dark_ml - " + str(num_dark_ml) + ";"))
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, green, blue and
    # dark potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT potions.item_sku FROM potions WHERE potions.inventory = 0;"))
        o = cur.fetchall()
        out_of_stock = []
        for item in o:
            out_of_stock.append(item[0])

    needed = []
    for potion in out_of_stock:
        with db.engine.begin() as connection:   
            cur = connection.execute(sqlalchemy.text("SELECT potions.red, potions.green, potions.blue, potions.dark FROM potions WHERE potions.item_sku = '" + potion + "';"))
            potion_type = cur.fetchone()
            potion_type_list = []
            for color in potion_type:
                potion_type_list.append(color)
            needed.append([potion, potion_type_list])

    plan = check_enough(needed)
    
    if plan == []:
        print("Not enough ml to make any of the out-of-stock potions.")
        with db.engine.begin() as connection:
            cur = connection.execute(sqlalchemy.text("SELECT potions.item_sku FROM potions WHERE potions.inventory > 0;"))
            h = cur.fetchall()
            in_stock = []
            for item in h:
                in_stock.append(item[0])
        
        wanted = []
        for potion in in_stock:
            with db.engine.begin() as connection:   
                cur = connection.execute(sqlalchemy.text("SELECT potions.red, potions.green, potions.blue, potions.dark FROM potions WHERE potions.item_sku = '" + potion + "';"))
                potion_type = cur.fetchone()
                potion_type_list = []
                for color in potion_type:
                    potion_type_list.append(color)
                wanted.append([potion, potion_type_list])
        plan = check_enough(wanted)
        if plan == []:
            print("Not enough ml to make any potions.")
        else:
            print("Enough ml to make some already stocked potions.")
    
    print("My Plan to Bottle Potions:", plan)
    return plan


if __name__ == "__main__":
    print(get_bottle_plan())