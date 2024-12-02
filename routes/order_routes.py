from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from extensions import db
from models import User, Buyer, Farmer, Product, Order, OrderItem, Cart, CartItem

order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/orders', methods=['POST'])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can place orders'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    data = request.get_json()
    delivery_address = data.get('delivery_address', buyer.default_delivery_address)
    payment_method = data.get('payment_method', buyer.preferred_payment_method)

    if not delivery_address:
        return jsonify({'error': 'Delivery address is required'}), 400
    if not payment_method:
        return jsonify({'error': 'Payment method is required'}), 400
    
    offer_id = data.get('offer_id')
    if offer_id:
        # Process order based on accepted offer
        offer = Offer.query.get(offer_id)
        if not offer or offer.status != 'accepted':
            return jsonify({'error': 'Invalid or unaccepted offer'}), 400
        # Ensure the offer belongs to the buyer
        if offer.buyer_id != buyer.user_id:
            return jsonify({'error': 'You are not authorized to use this offer'}), 403

        product = offer.product
        if not product.is_active:
            return jsonify({'error': 'Product not available'}), 400
        quantity = data.get('quantity', 1)
        if product.quantity_available < quantity:
            return jsonify({'error': 'Insufficient product quantity available'}), 400

        # Create order with offer price
        total_amount = offer.offer_price * quantity
        order = Order(
            buyer_id=buyer.user_id,
            total_amount=total_amount,
            payment_status='pending',  # Update after integrating payment gateway
            delivery_address=delivery_address,
            status='placed',
            payment_method=payment_method
        )
        db.session.add(order)
        db.session.flush()  # Get order.id

        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            farmer_id=product.farmer_id,
            quantity=quantity,
            price=offer.offer_price,
            subtotal=total_amount
        )
        db.session.add(order_item)

        # Update product quantity
        product.quantity_available -= quantity
        if product.quantity_available == 0:
            product.is_active = False

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error placing order: {e}")
            return jsonify({'error': 'An error occurred while placing the order'}), 500

        return jsonify({'message': 'Order placed successfully', 'order_id': order.id}), 201
    else:

      cart = Cart.query.filter_by(buyer_id=buyer.user_id).first()
      if not cart or cart.items.count() == 0:
          return jsonify({'error': 'Your cart is empty'}), 400

      # Calculate total amount and create order
      total_amount = 0
      order_items_data = []
      for cart_item in cart.items:
          product = cart_item.product
          if not product.is_active:
              return jsonify({'error': f'Product {product.name} is no longer available'}), 400
          if product.quantity_available < cart_item.quantity:
              return jsonify({'error': f'Insufficient quantity for product {product.name}'}), 400
          subtotal = product.price * cart_item.quantity
          total_amount += subtotal
          order_items_data.append({
              'product_id': product.id,
              'farmer_id': product.farmer_id,
              'quantity': cart_item.quantity,
              'price': product.price,
              'subtotal': subtotal
          })

      order = Order(
          buyer_id=buyer.user_id,
          total_amount=total_amount,
          payment_status='pending',  # Update after integrating payment gateway
          delivery_address=delivery_address,
          status='placed',
          payment_method=payment_method
      )
      db.session.add(order)
      db.session.flush()  # Get order.id

      # Create order items and update product quantities
      for item_data in order_items_data:
          order_item = OrderItem(
              order_id=order.id,
              product_id=item_data['product_id'],
              farmer_id=item_data['farmer_id'],
              quantity=item_data['quantity'],
              price=item_data['price'],
              subtotal=item_data['subtotal']
          )
          db.session.add(order_item)

          # Update product quantity
          product = Product.query.get(item_data['product_id'])
          product.quantity_available -= item_data['quantity']
          if product.quantity_available == 0:
              product.is_active = False  # Mark product as inactive if out of stock

      try:
          # Clear buyer's cart
          CartItem.query.filter_by(cart_id=cart.id).delete()
          db.session.commit()
      except SQLAlchemyError as e:
          db.session.rollback()
          print(f"Error placing order: {e}")
          return jsonify({'error': 'An error occurred while placing the order'}), 500

    return jsonify({'message': 'Order placed successfully', 'order_id': order.id}), 201

@order_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.role == 'buyer':
        orders = Order.query.filter_by(buyer_id=user_id).order_by(Order.created_at.desc()).all()
    elif user.role == 'farmer':
        # For farmers, get orders containing their products
        orders = Order.query.join(OrderItem).filter(OrderItem.farmer_id == user_id).order_by(Order.created_at.desc()).all()
    else:
        return jsonify({'error': 'Invalid user role'}), 403

    orders_data = []
    for order in orders:
        orders_data.append({
            'order_id': order.id,
            'total_amount': str(order.total_amount),
            'status': order.status,
            'payment_status': order.payment_status,
            'delivery_address': order.delivery_address,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat()
        })

    return jsonify({'orders': orders_data}), 200

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    # Check if the user is authorized to view the order
    if user.role == 'buyer' and order.buyer_id != user_id:
        return jsonify({'error': 'You are not authorized to view this order'}), 403
    elif user.role == 'farmer':
        # Check if the order contains items from this farmer
        items = OrderItem.query.filter_by(order_id=order.id, farmer_id=user_id).all()
        if not items:
            return jsonify({'error': 'You are not authorized to view this order'}), 403

    # Fetch order items
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    items_data = []
    for item in order_items:
        product = item.product
        items_data.append({
            'order_item_id': item.id,
            'product_id': product.id,
            'product_name': product.name,
            'quantity': item.quantity,
            'price': str(item.price),
            'subtotal': str(item.subtotal),
            'farmer_id': item.farmer_id
        })

    order_data = {
        'order_id': order.id,
        'total_amount': str(order.total_amount),
        'status': order.status,
        'payment_status': order.payment_status,
        'delivery_address': order.delivery_address,
        'payment_method': order.payment_method,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
        'items': items_data
    }

    return jsonify(order_data), 200

@order_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({'error': 'Status is required'}), 400

    # Define allowable status transitions
    valid_statuses = ['placed', 'confirmed', 'dispatched', 'delivered', 'cancelled']

    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400

    # Only the buyer or relevant farmer can update the order status
    if user.role == 'buyer':
        if order.buyer_id != user_id:
            return jsonify({'error': 'You are not authorized to update this order'}), 403
        # Buyers can cancel their orders before they are dispatched
        if new_status == 'cancelled' and order.status in ['placed', 'confirmed']:
            order.status = new_status
        else:
            return jsonify({'error': 'You cannot change the order to this status'}), 403
    elif user.role == 'farmer':
        # Farmers can update the status of order items that involve them
        items = OrderItem.query.filter_by(order_id=order.id, farmer_id=user_id).all()
        if not items:
            return jsonify({'error': 'You are not authorized to update this order'}), 403

        # Update status for individual items or overall order status if applicable
        if new_status in ['confirmed', 'dispatched', 'delivered']:
            # For simplicity, we'll update the overall order status
            order.status = new_status
        else:
            return jsonify({'error': 'You cannot change the order to this status'}), 403
    else:
        return jsonify({'error': 'Invalid user role'}), 403

    order.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating order status: {e}")
        return jsonify({'error': 'An error occurred while updating order status'}), 500

    return jsonify({'message': f'Order status updated to {new_status}'}), 200
