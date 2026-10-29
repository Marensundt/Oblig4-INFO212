"""The visitor's cart in the Flask session, shared by the shop (C2) and checkout (C3) controllers."""
from flask import session

from app.models.cart import Cart

# Session key of the cart; kept when the visitor logs in (account.KEPT_ON_LOGIN, US-11 AC2).
CART_KEY = "cart"


def load_cart():
    return Cart.from_session(session.get(CART_KEY))


def save_cart(cart):
    session[CART_KEY] = cart.to_session()


def clear_cart():
    session.pop(CART_KEY, None)
