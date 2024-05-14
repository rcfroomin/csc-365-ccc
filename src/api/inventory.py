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
    gold = get_current_balance("gold")
    green_ml = get_current_balance("green_ml")
    red_ml = get_current_balance("red_ml")
    blue_ml = get_current_balance("blue_ml")
    dark_ml = get_current_balance("dark_ml")
    potions_list = find_in_stock_potions()

    total = len(potions_list)
    
    return {"number_of_potions": total, "ml_in_barrels": (green_ml + red_ml + blue_ml + dark_ml), "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    gold = get_current_balance("gold")
    
    potion_capacity = 0
    ml_capacity = 0
    
    if gold >= 2000 and (get_total_potions_in_inventory() >= 45) and (get_total_ml_in_inventory() >= 8000):
        potion_capacity += 1
        ml_capacity += 1
        print("Want to buy 1 more ml_capacity and 1 more potion_capacity")
    elif gold >= 1000 and (get_total_potions_in_inventory() >= 45):
        potion_capacity += 1
        print("Want to buy 1 more potion_capacity")
    elif gold >= 1000 and (get_total_ml_in_inventory() >= 5000):
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
    green_ml = get_current_balance("green_ml")
    red_ml = get_current_balance("red_ml")
    blue_ml = get_current_balance("blue_ml")
    dark_ml = get_current_balance("dark_ml")

    return (green_ml + red_ml + blue_ml + dark_ml)

def get_total_potions_in_inventory():
    total = 0
    in_stock_potions = find_in_stock_potions()
    for potion in in_stock_potions:
        total += get_current_balance(potion)
    
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
            account_transaction_id = update_balance("gold", -1000 * capacity_purchase.ml_capacity, None, "I Purchased " + str(capacity_purchase.ml_capacity) + " ml capacity", None)
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET ml_capacity = (global_inventory.ml_capacity + " + str(capacity_purchase.ml_capacity) + ");"))
        if capacity_purchase.potion_capacity > 0:
            account_transaction_id = update_balance("gold", -1000 * capacity_purchase.potion_capacity, None, "I Purchased " + str(capacity_purchase.potion_capacity) + " potion capacity", None)
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET potion_capacity = (global_inventory.potion_capacity + " + str(capacity_purchase.potion_capacity) + ");"))
    return "OK"

def update_balance(account_name: str, change: int, customer_name: str, description: str, account_transaction_id): #UPDATED FOR V4
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

def find_in_stock_potions():
    catalog = []
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT potions.item_sku FROM potions;"))
        potion_list = cur.fetchall()
        
        for potion in potion_list:
            balance = get_current_balance(potion[0])
            if balance > 0:
                catalog.append(potion[0])
    
    return catalog
