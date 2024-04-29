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
    potions_list = build_recipe_list()
    for potion in potions_list:
        balance = get_current_balance(potion[0])
        if balance > 0:
            catalog.append(
                {
                    "sku": potion[0],
                    "name": potion[0],
                    "quantity": balance,
                    "price": 55,
                    "potion_type": potion[1],
                }
            )
    print("My Catalog of Potions for Sale:", catalog)
    return catalog


def get_current_balance(account_name: str):
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT accounts.account_id FROM accounts WHERE accounts.account_name = '" + account_name + "';"))
        row1 = cur.fetchone()
        account_id = row1[0]

    balance  = 0
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT account_ledger_entries.change FROM account_ledger_entries WHERE account_ledger_entries.account_id = '" + str(account_id) + "';"))
        transactions = cur.fetchall()
        
        for transaction in transactions:
            balance += transaction[0]
    
    return balance


def build_recipe_list(): 
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
