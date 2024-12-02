from flask import Blueprint

auth_bp = Blueprint('auth_bp', __name__)
product_bp = Blueprint('product_bp', __name__)
profile_bp = Blueprint('profile_bp', __name__)
cart_bp = Blueprint('cart_bp', __name__)
order_bp = Blueprint('order_bp', __name__)
chat_bp = Blueprint('chat_bp', __name__)

from . import auth_routes, product_routes, cart_routes, profile_routes, order_routes