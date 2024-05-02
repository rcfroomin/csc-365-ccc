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

def update_balance(account_name: str, change: int, customer_name: str, description: str, account_transaction_id): 
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT accounts.account_id FROM accounts WHERE accounts.account_name = '" + account_name + "';"))
        row1 = cur.fetchone()
        account_id = row1[0]

    with db.engine.begin() as connection:
        if account_transaction_id == None: # Create a new account transation in the table and get its id
            if customer_name:
                result = connection.execute(sqlalchemy.text("INSERT INTO account_transactions_table (customer_name, description) VALUES ('" + customer_name + "', '" + description + "');"))
            else:
                result = connection.execute(sqlalchemy.text("INSERT INTO account_transactions_table (description) VALUES ('" + description + "');"))
            cur = connection.execute(sqlalchemy.text("SELECT account_transactions_table.id FROM account_transactions_table WHERE account_transactions_table.description = '" + description + "' ORDER BY created_at desc;"))
            account_transaction_id = cur.first()[0]
        result = connection.execute(sqlalchemy.text("INSERT INTO account_ledger_entries (account_id, account_transaction_id, change) VALUES (" + str(account_id) + ", " + str(account_transaction_id) + ", " + str(change) + ");"))
    return account_transaction_id 

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

def ml_inv(): 
    num_red_ml = get_current_balance("red_ml")
    num_green_ml = get_current_balance("green_ml")
    num_blue_ml = get_current_balance("blue_ml")
    num_dark_ml = get_current_balance("dark_ml")
    return [num_green_ml, num_red_ml, num_blue_ml, num_dark_ml]

def check_enough(needed: list): # needed = list[potion_sku, potion_type]
    plan = []
    num_red_ml = get_current_balance("red_ml")
    num_green_ml = get_current_balance("green_ml")
    num_blue_ml = get_current_balance("blue_ml")
    num_dark_ml = get_current_balance("dark_ml")

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
                num_red_ml =item[1][0]
                num_green_ml = item[1][1]
                num_blue_ml = item[1][2]
                num_dark_ml = item[1][3]
                description = str(item[0]) + " bottled and delivered to me."
                account_transaction_id = update_balance(item[0], potion.quantity, None, description, None)
                if num_red_ml > 0:
                    update_balance("red_ml", (-1 * num_red_ml), None, description, account_transaction_id)
                if num_green_ml > 0:
                    update_balance("green_ml", (-1 * num_green_ml), None, description, account_transaction_id)
                if num_blue_ml > 0:
                    update_balance("blue_ml", (-1 * num_blue_ml), None, description, account_transaction_id)
                if num_dark_ml > 0:
                    update_balance("dark_ml", (-1 * num_dark_ml), None, description, account_transaction_id)
    return "OK"

@router.post("/plan")
def get_bottle_plan(): 
    """
    Go from barrel to bottle.
    """
    # Each bottle has a quantity of what proportion of red, green, blue and
    # dark potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.    
    inv = build_inventory()
    out_of_stock = []
    for potion in inv:
        balance = get_current_balance(potion[0])
        if balance == 0:
            out_of_stock.append(potion[0])

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
        in_stock = []
        for potion in inv:
            balance = get_current_balance(potion[0])
            if balance > 0:
                in_stock.append(potion[0])
        
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
        if (plan == []):
            print("Not enough ml to make any potions.")
        else:
            print("Enough ml to make some already stocked potions.")
    
    print("My Plan to Bottle Potions:", plan)
    return plan


if __name__ == "__main__":
    print(get_bottle_plan())