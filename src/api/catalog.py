from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        row1 = cur.fetchone()
        num_green_potions_num = row1[0]
        num_red_potions_num = row1[3]
        num_blue_potions_num = row1[4]
        cur.close()
    return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green_potions_num,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            },
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red_potions_num,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            },
            {
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": num_blue_potions_num,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            }
        ]
