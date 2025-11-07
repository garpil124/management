from db.mongo import users_col, payments_col, products_col

# User
async def add_user(user_id, data):
    return await users_col.update_one(
        {"_id": user_id}, {"$set": data}, upsert=True
    )

async def get_user(user_id):
    return await users_col.find_one({"_id": user_id})

# Payments
async def create_payment(payment_data):
    return await payments_col.insert_one(payment_data)

# Products
async def add_product(prod):
    return await products_col.insert_one(prod)

async def list_products():
    return await products_col.find({}).to_list(50)
