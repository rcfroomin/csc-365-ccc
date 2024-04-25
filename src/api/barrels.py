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
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))
        elif barrel.potion_type == [1, 0, 0, 0]:
            quantity = barrel.ml_per_barrel
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))
        elif barrel.potion_type == [0, 0, 1, 0]:
            quantity = barrel.ml_per_barrel
            price = barrel.price
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + " + str(quantity) + ";"))
                result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(price) + ";"))

    return "OK"

def get_value(barrel: Barrel):
    return (barrel.ml_per_barrel / barrel.price)

def get_best_value_barrel(wholesale_catalog: list[Barrel]):
    if wholesale_catalog == None or len(wholesale_catalog) == 0:
        return None
    else:
        with db.engine.begin() as connection:
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_gold = row1[1]
    
        best_value = None
        ml_needed = what_ml_do_i_need()
        i = 0
        while (best_value == None):
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
    with db.engine.begin() as connection:
        cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
        row1 = cur.fetchone()
        num_green_ml = row1[0]
        num_red_ml = row1[2]
        num_blue_ml = row1[3]
        num_dark_ml = row1[4]
    
    inv = [[[1, 0, 0, 0], num_red_ml], [[0, 1, 0, 0], num_green_ml], [[0, 0, 1, 0], num_blue_ml], [[0, 0, 0, 1], num_dark_ml]]
    for ml in inv:
        if ml[1] > 200:
            inv.remove(ml)
    
    i = 0
    for i in range(len(inv)):
        inv[i]=inv[i][0]
        i += 1
    
    print("Ml types I need more of: ", inv)
    return inv # returns a list of potion types i have less than 200 ml of
    
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
                cur = connection.execute(sqlalchemy.text("SELECT * from global_inventory;"))
                row1 = cur.fetchone()
                num_gold = row1[1]
                cur = connection.execute(sqlalchemy.text("SELECT potions.inventory FROM potions WHERE potions.item_sku = 'Red_Potion';"))
                red_potion = cur.fetchone()
                num_red_potions = red_potion[0]
                cur = connection.execute(sqlalchemy.text("SELECT potions.inventory FROM potions WHERE potions.item_sku = 'Green_Potion';"))
                green_potion = cur.fetchone()
                num_green_potions = green_potion[0]
                cur = connection.execute(sqlalchemy.text("SELECT potions.inventory FROM potions WHERE potions.item_sku = 'Blue_Potion';"))
                blue_potion = cur.fetchone()
                num_blue_potions = blue_potion[0]
    
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
