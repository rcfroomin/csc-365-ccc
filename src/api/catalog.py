from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []

    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT potions.item_sku FROM potions WHERE potions.inventory > 0;"))
        for_sale = cur.fetchall()
        
        for item in for_sale:
            cur = connection.execute(sqlalchemy.text("SELECT potions.inventory FROM potions WHERE potions.item_sku = '" + item[0] + "';"))
            inventory = cur.fetchone()
            cur = connection.execute(sqlalchemy.text("SELECT potions.red, potions.green, potions.blue, potions.dark FROM potions WHERE potions.item_sku = '" + item[0] + "';"))
            potion_type = cur.fetchone()
            potion_type_list = []
            for color in potion_type:
                potion_type_list.append(color)
            catalog.append(
            {
                "sku": item[0],
                "name": item[0],
                "quantity": inventory[0],
                "price": 55,
                "potion_type": potion_type_list,
            }
        )
    print("My Catalog of Potions for Sale:", catalog)
    return catalog
