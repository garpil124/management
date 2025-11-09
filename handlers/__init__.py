# small helper - we expect main.py to import handlers.register_all_handlers()
from .start import register_start
from .menu import register_menu
from .product import register_product
from .owner import register_owner
from .subowner import register_subowner
from .payment import register_payment
from .callback import register_callback_handlers
from . import tagall_admin

def register_all_handlers(app):
    # order matters: callback registration first so callbacks resolve
    register_callback_handlers(app)
    register_start(app)
    register_menu(app)
    register_product(app)
    register_owner(app)
    register_subowner(app)
    register_payment(app)
