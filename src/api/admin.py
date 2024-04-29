from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

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

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("DELETE FROM account_ledger_entries"))
        cur = connection.execute(sqlalchemy.text("DELETE FROM account_transactions_table"))
        account_transaction_id = update_balance("gold", 100, None, "Reset game state", None)
        update_balance("red_ml", 0, None, "Reset game state", account_transaction_id)
        update_balance("green_ml", 0, None, "Reset game state", account_transaction_id)
        update_balance("blue_ml", 0, None, "Reset game state", account_transaction_id)
        update_balance("dark_ml", 0, None, "Reset game state", account_transaction_id)
    return "OK"

