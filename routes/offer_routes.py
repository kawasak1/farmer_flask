from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from extensions import db
from models import User, Buyer, Farmer, Product, Offer

offer_bp = Blueprint('offer_bp', __name__)

@offer_bp.route('/offers', methods=['POST'])
@jwt_required()
def create_offer():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can make offers'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    data = request.get_json()
    product_id = data.get('product_id')
    offer_price = data.get('offer_price')

    if not product_id or offer_price is None:
        return jsonify({'error': 'Product ID and offer price are required'}), 400

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'error': 'Product not found or not available'}), 404

    offer = Offer(
        product_id=product_id,
        buyer_id=buyer.user_id,
        offer_price=offer_price,
        status='pending'
    )

    db.session.add(offer)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating offer: {e}")
        return jsonify({'error': 'An error occurred while creating the offer'}), 500

    return jsonify({'message': 'Offer submitted successfully', 'offer_id': offer.id}), 201

@offer_bp.route('/offers/<int:offer_id>', methods=['PUT'])
@jwt_required()
def respond_to_offer(offer_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'farmer':
        return jsonify({'error': 'Only farmers can respond to offers'}), 403

    farmer = Farmer.query.get(user_id)
    if not farmer:
        return jsonify({'error': 'Farmer profile not found'}), 404

    offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404

    # Check if the farmer owns the product
    if offer.product.farmer_id != farmer.user_id:
        return jsonify({'error': 'You are not authorized to respond to this offer'}), 403

    data = request.get_json()
    action = data.get('action')

    if action not in ['accept', 'reject', 'counter']:
        return jsonify({'error': 'Invalid action. Must be accept, reject, or counter'}), 400

    if action == 'accept':
        offer.status = 'accepted'
    elif action == 'reject':
        offer.status = 'rejected'
    elif action == 'counter':
        counter_price = data.get('counter_price')
        if counter_price is None:
            return jsonify({'error': 'Counter price is required for counter offers'}), 400
        offer.offer_price = counter_price
        offer.status = 'countered'
    else:
        return jsonify({'error': 'Invalid action'}), 400

    offer.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error responding to offer: {e}")
        return jsonify({'error': 'An error occurred while responding to the offer'}), 500

    return jsonify({'message': f'Offer {action}ed successfully'}), 200

@offer_bp.route('/offers', methods=['GET'])
@jwt_required()
def get_offers():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.role == 'buyer':
        offers = Offer.query.filter_by(buyer_id=user.id).order_by(Offer.created_at.desc()).all()
    elif user.role == 'farmer':
        # Get offers for products owned by the farmer
        offers = Offer.query.join(Product).filter(Product.farmer_id == user.id).order_by(Offer.created_at.desc()).all()
    else:
        return jsonify({'error': 'Invalid user role'}), 403

    offers_data = []
    for offer in offers:
        offers_data.append({
            'offer_id': offer.id,
            'product_id': offer.product_id,
            'product_name': offer.product.name,
            'offer_price': str(offer.offer_price),
            'status': offer.status,
            'buyer_id': offer.buyer_id,
            'farmer_id': offer.product.farmer_id,
            'created_at': offer.created_at.isoformat(),
            'updated_at': offer.updated_at.isoformat()
        })

    return jsonify({'offers': offers_data}), 200

@offer_bp.route('/offers/<int:offer_id>/buyer_response', methods=['PUT'])
@jwt_required()
def buyer_response_to_offer(offer_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can respond to offers'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    offer = Offer.query.get(offer_id)
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404

    if offer.buyer_id != buyer.user_id:
        return jsonify({'error': 'You are not authorized to respond to this offer'}), 403

    data = request.get_json()
    action = data.get('action')

    if action not in ['accept', 'reject', 'counter']:
        return jsonify({'error': 'Invalid action. Must be accept, reject, or counter'}), 400

    if action == 'accept':
        offer.status = 'accepted'
    elif action == 'reject':
        offer.status = 'rejected'
    elif action == 'counter':
        counter_price = data.get('counter_price')
        if counter_price is None:
            return jsonify({'error': 'Counter price is required for counter offers'}), 400
        offer.offer_price = counter_price
        offer.status = 'pending'  # Back to pending for farmer to respond
    else:
        return jsonify({'error': 'Invalid action'}), 400

    offer.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error responding to offer: {e}")
        return jsonify({'error': 'An error occurred while responding to the offer'}), 500

    return jsonify({'message': f'Offer {action}ed successfully'}), 200

