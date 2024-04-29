import random
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

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

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name) VALUES ('" + new_cart.customer_name + "');"))
        cur = connection.execute(sqlalchemy.text("SELECT carts.cart_id FROM carts WHERE carts.customer_name = '" + new_cart.customer_name + "' ORDER BY created_at desc;"))
        cart_id = cur.first()[0]
    
    print("cart_id: " + str(cart_id) + " created for customer: " + new_cart.customer_name)
    return {"cart_id": int(cart_id)}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT potions.price FROM potions WHERE potions.item_sku = '" + item_sku + "';"))
        price = cur.first()[0]
        cur = connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, item_sku, quantity, price) VALUES (" + str(cart_id) + ", '" + item_sku + "', " + str(cart_item.quantity) + ", " + str(price) + ");"))
    
    print("cart_id: " + str(cart_id) + " added " + str(cart_item.quantity) + " of item_sku: " + item_sku)
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT (cart_items.item_sku, cart_items.quantity, price) FROM cart_items WHERE cart_items.cart_id = '" + str(cart_id) + "';"))
        items = cur.fetchall()
    
    total_quantity = 0
    for item in items:
        item_sku, quantity, price = item[0].strip("()").split(',')
        total_quantity += int(quantity)
        
        with db.engine.begin() as connection:
            cur = connection.execute(sqlalchemy.text("SELECT carts.customer_name FROM carts WHERE carts.cart_id = '" + str(cart_id) + "' ORDER BY created_at desc;"))
            customer_name = cur.first()[0]
        
        description = customer_name + " bought " + str(quantity) + " of " + item_sku + " for " + str(int(quantity) * int(price)) + " gold"

        account_transaction_id = update_balance("gold", int(quantity) * int(price), customer_name, description, None)
        update_balance(item_sku, -1 * int(quantity), customer_name, description, account_transaction_id)
    
    print("cart_id: " + str(cart_id) + " checked out with total quantity: " + str(total_quantity) + " and total payment: " + str(int(quantity) * int(price)))
    return {"total_potions_bought": total_quantity, "total_gold_paid": int(int(quantity) * int(price))}
