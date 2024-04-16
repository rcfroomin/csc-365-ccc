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

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    for potion in potions_delivered:
        if potion.potion_type == [0, 100, 0, 0]:
            p_quantity = potion.quantity
            ml_quantity = potion.quantity * 100
            print(f"successfuly made {p_quantity} potions and used {ml_quantity} ml of green potion.")
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + " + str(p_quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - " + str(ml_quantity) + ";"))
        if potion.potion_type == [100, 0, 0, 0]:
            p_quantity = potion.quantity
            ml_quantity = potion.quantity * 100
            print(f"successfuly made {p_quantity} potions and used {ml_quantity} ml of red potion.")
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions + " + str(p_quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - " + str(ml_quantity) + ";"))
        if potion.potion_type == [0, 0, 100, 0]:
            p_quantity = potion.quantity
            ml_quantity = potion.quantity * 100
            print(f"successfuly made {p_quantity} potions and used {ml_quantity} ml of blue potion.")
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions + " + str(p_quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml - " + str(ml_quantity) + ";"))
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
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_green_ml = row1[1]
                num_red_ml = row1[5]
                num_blue_ml = row1[6]
                cur.close()
    num_g_bottles_to_make = num_green_ml // 100
    num_r_bottles_to_make = num_red_ml // 100
    num_b_bottles_to_make = num_blue_ml // 100
    print("Attempting to mix {num_g_bottles_to_make} green, {num_r_bottles_to_make} red, and {num_b_bottles_to_make} blue potions.")
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