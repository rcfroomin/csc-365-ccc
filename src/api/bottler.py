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
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + :quantity ;"), quantity=potion.quantity)
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - :quantity ;"), quantity=(potion.quantity * 100))
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
                #num_green_ml_inv = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_green_ml = row1[1]
                cur.close()
    num_bottles_to_make = num_green_ml // 100

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": num_bottles_to_make,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())