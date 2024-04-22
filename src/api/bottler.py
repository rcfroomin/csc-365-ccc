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

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
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
        #instead of select * use cons
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        #num_green_ml = row1.num_green_ml
        row1 = cur.fetchone()
        num_green_ml = row1[1]
        num_red_ml = row1[5]
        num_blue_ml = row1[6]
    num_g_bottles_to_make = num_green_ml // 100
    num_r_bottles_to_make = num_red_ml // 100
    num_b_bottles_to_make = num_blue_ml // 100
    print(f"Attempting to mix {num_g_bottles_to_make} green, {num_r_bottles_to_make} red, and {num_b_bottles_to_make} blue potions.")
    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": num_g_bottles_to_make,
            },
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": num_r_bottles_to_make,
            },
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": num_b_bottles_to_make,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())