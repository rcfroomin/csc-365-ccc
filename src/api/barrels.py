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
            account_transaction_id = update_balance("green_ml", quantity, None, "Green barrel delivered to me", None)
            update_balance("gold", -1 * price, None, "Green barrel delivered to me", account_transaction_id)
        elif barrel.potion_type == [1, 0, 0, 0]:
            quantity = barrel.ml_per_barrel
            price = barrel.price
            account_transaction_id = update_balance("red_ml", quantity, None, "Red barrel delivered to me", None)
            update_balance("gold", -1 * price, None, "Red barrel delivered to me", account_transaction_id)
        elif barrel.potion_type == [0, 0, 1, 0]:
            quantity = barrel.ml_per_barrel
            price = barrel.price
            account_transaction_id = update_balance("blue_ml", quantity, None, "Blue barrel delivered to me", None)
            update_balance("gold", -1 * price, None, "Blue barrel delivered to me", account_transaction_id)
        elif barrel.potion_type == [0, 0, 0, 1]:
            quantity = barrel.ml_per_barrel
            price = barrel.price
            account_transaction_id = update_balance("dark_ml", quantity, None, "Dark barrel delivered to me", None)
            update_balance("gold", -1 * price, None, "Dark barrel delivered to me", account_transaction_id)
    return "OK"

def get_value(barrel: Barrel):
    return (barrel.ml_per_barrel / barrel.price)

def get_best_value_barrel(wholesale_catalog: list[Barrel]):
    if wholesale_catalog == None or len(wholesale_catalog) == 0:
        return None
    else:
        num_gold = get_current_balance("gold")
    
        best_value = None
        ml_needed = what_ml_do_i_need()
        #print("Ml types I need more of: ", ml_needed)

        i = 0
        while (best_value == None and wholesale_catalog[i]):
            if (wholesale_catalog[i].potion_type in ml_needed): # my algorithm needs to start with a barrel that is a potion type i need in order for it to work correctly
                best_value = wholesale_catalog[i]
            i += 1
        
        for barrel in wholesale_catalog:
            if (get_value(barrel) > get_value(best_value)) and (barrel.potion_type in ml_needed): # check that barrel in question is better than best barrel so far and then check to make sure its a potion type i need
                best_value = barrel
        
        while (wholesale_catalog and best_value and num_gold < best_value.price):
            wholesale_catalog.remove(best_value) #remove a best barrel if i can't afford it
            best_value = get_best_value_barrel(wholesale_catalog) # find the next best barrel
    
        if (best_value and ((best_value.ml_per_barrel / best_value.price) > 1.82)): # make sure i'm not losing gold bc all my potions are 100ml and cost 55 gold
            return best_value
        elif (wholesale_catalog and best_value):
            get_best_value_barrel(wholesale_catalog.remove(best_value))
        else:
            return None

def what_ml_do_i_need(): # returns a list of potion types i have less than 200 ml of
    num_green_ml = get_current_balance("green_ml")
    num_red_ml = get_current_balance("red_ml")
    num_blue_ml = get_current_balance("blue_ml")
    num_dark_ml = get_current_balance("dark_ml")
    
    inv = [[[1, 0, 0, 0], num_red_ml], [[0, 1, 0, 0], num_green_ml], [[0, 0, 1, 0], num_blue_ml], [[0, 0, 0, 1], num_dark_ml]]
    for ml in inv:
        if ml[1] > 200:
            inv.remove(ml)
    
    i = 0
    for i in range(len(inv)):
        inv[i]=inv[i][0]
        i += 1
    
    return inv # returns a list of potion types i have less than 200 ml of

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

def get_current_balance(account_name: str): #UPDATED FOR V4
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
    
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    num_gold = get_current_balance("gold")
    
    print(f"wholesale catalog: {wholesale_catalog}")
    
    best_barrel = get_best_value_barrel(wholesale_catalog)
    
    if best_barrel == None:
        print("No barrels in the catalog I wouldn't lose money on when selling for 55 gold.")
        return []
    
    print(f"best barrel i can afford: {best_barrel}")

    if num_gold >= best_barrel.price:
        print(f"want to buy {best_barrel.sku}")
        return [
            {
                "sku": best_barrel.sku,
                "quantity": 1
            }
        ]
    else:
        return []
