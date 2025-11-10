from .owner_cb import register_owner_callback
from .payment_cb import register_payment_callback
from .subowner_cb import register_subowner_callback
from .user_cb import register_user_callback

def register_callback_handlers(app):
    register_owner_callback(app)
    register_payment_callback(app)
    register_subowner_callback(app)
    register_user_callback(app)
