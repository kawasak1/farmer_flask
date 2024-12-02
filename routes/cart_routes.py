from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User, Buyer, Product, Cart, CartItem

cart_bp = Blueprint('cart_bp', __name__)

# Helper function to get or create a cart for a buyer
def get_or_create_cart(buyer_id):
    cart = Cart.query.filter_by(buyer_id=buyer_id).first()
    if not cart:
        cart = Cart(buyer_id=buyer_id)
        db.session.add(cart)
        db.session.commit()
    return cart

@cart_bp.route('/cart/items', methods=['POST'])
@jwt_required()
def add_item_to_cart():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can add items to cart'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'error': 'Product not found or not available'}), 404

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    if product.quantity_available < quantity:
        return jsonify({'error': 'Insufficient product quantity available'}), 400

    cart = get_or_create_cart(buyer.user_id)
    # Check if the product is already in the cart
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error adding item to cart: {e}")
        return jsonify({'error': 'An error occurred while adding item to cart'}), 500

    return jsonify({'message': 'Item added to cart successfully'}), 201

@cart_bp.route('/cart', methods=['GET'])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can view cart'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    cart = get_or_create_cart(buyer.user_id)
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()

    items = []
    for item in cart_items:
        product = item.product
        items.append({
            'cart_item_id': item.id,
            'product_id': product.id,
            'product_name': product.name,
            'price': str(product.price),
            'quantity': item.quantity,
            'quantity_unit': product.quantity_unit,
            'subtotal': str(product.price * item.quantity),
            'farmer_id': product.farmer_id,
            'image_url': product.images.first().image_url if product.images.first() else None
        })

    return jsonify({'cart_id': cart.id, 'items': items}), 200

@cart_bp.route('/cart/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can update cart items'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    data = request.get_json()
    quantity = data.get('quantity')

    if quantity is None or quantity <= 0:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    cart = get_or_create_cart(buyer.user_id)
    cart_item = CartItem.query.filter_by(cart_id=cart.id, id=item_id).first()

    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404

    product = cart_item.product
    if product.quantity_available < quantity:
        return jsonify({'error': 'Insufficient product quantity available'}), 400

    cart_item.quantity = quantity

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating cart item: {e}")
        return jsonify({'error': 'An error occurred while updating cart item'}), 500

    return jsonify({'message': 'Cart item updated successfully'}), 200

@cart_bp.route('/cart/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_cart_item(item_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can remove cart items'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    cart = get_or_create_cart(buyer.user_id)
    cart_item = CartItem.query.filter_by(cart_id=cart.id, id=item_id).first()

    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404

    try:
        db.session.delete(cart_item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error removing cart item: {e}")
        return jsonify({'error': 'An error occurred while removing cart item'}), 500

    return jsonify({'message': 'Cart item removed successfully'}), 200

