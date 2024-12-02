from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os

from extensions import db
from models import User, Farmer, Buyer

from schemas import UserProfileSchema, UpdateUserProfileSchema, FarmerProfileSchema, UpdateFarmerProfileSchema, BuyerProfileSchema, UpdateBuyerProfileSchema

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_schema = UserProfileSchema()
    user_data = user_schema.dump(user)

    # Include role-specific data
    if user.role == 'farmer':
        farmer = Farmer.query.get(user_id)
        if farmer:
            farmer_schema = FarmerProfileSchema()
            farmer_data = farmer_schema.dump({'user': user_data, **farmer.__dict__})
            return jsonify(farmer_data), 200
    elif user.role == 'buyer':
        buyer = Buyer.query.get(user_id)
        if buyer:
            buyer_schema = BuyerProfileSchema()
            buyer_data = buyer_schema.dump({'user': user_data, **buyer.__dict__})
            return jsonify(buyer_data), 200
    else:
        return jsonify(user_data), 200

@profile_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    schema = UpdateUserProfileSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Update user fields
    if 'username' in data:
        if User.query.filter(User.username == data['username'], User.id != user_id).first():
            return jsonify({'error': 'Username is already taken'}), 409
        user.username = data['username']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone_number' in data:
        user.phone_number = data['phone_number']
    if 'profile_picture_url' in data:
        user.profile_picture_url = data['profile_picture_url']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while updating the profile'}), 500

    return jsonify({'message': 'Profile updated successfully'}), 200

@profile_bp.route('/farm', methods=['PUT'])
@jwt_required()
def update_farm_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'farmer':
        return jsonify({'error': 'Only farmers can update farm profile'}), 403

    farmer = Farmer.query.get(user_id)
    if not farmer:
        return jsonify({'error': 'Farmer profile not found'}), 404

    data = request.get_json()
    schema = UpdateFarmerProfileSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Update farmer fields
    if 'farm_name' in data:
        farmer.farm_name = data['farm_name']
    if 'farm_size' in data:
        farmer.farm_size = data['farm_size']
    if 'farm_address' in data:
        farmer.farm_address = data['farm_address']
    if 'farm_description' in data:
        farmer.farm_description = data['farm_description']
    if 'crops_grown' in data:
        farmer.crops_grown = data['crops_grown']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while updating the farm profile'}), 500

    return jsonify({'message': 'Farm profile updated successfully'}), 200

@profile_bp.route('/delivery_preferences', methods=['PUT'])
@jwt_required()
def update_delivery_preferences():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'buyer':
        return jsonify({'error': 'Only buyers can update delivery preferences'}), 403

    buyer = Buyer.query.get(user_id)
    if not buyer:
        return jsonify({'error': 'Buyer profile not found'}), 404

    data = request.get_json()
    schema = UpdateBuyerProfileSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Update buyer fields
    if 'default_delivery_address' in data:
        buyer.default_delivery_address = data['default_delivery_address']
    if 'preferred_payment_method' in data:
        buyer.preferred_payment_method = data['preferred_payment_method']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while updating delivery preferences'}), 500

    return jsonify({'message': 'Delivery preferences updated successfully'}), 200

@profile_bp.route('/profile_picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['profile_picture']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Validate file extension
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
        return jsonify({'error': 'Invalid file type'}), 400

    # Save the file
    filename = f"profile_{user_id}{file_ext}"
    file_path = os.path.join(current_app.config['UPLOAD_PATH'], filename)
    file.save(file_path)

    # Update user's profile_picture_url
    # Assuming you serve static files from '/static/uploads/'
    file_url = f"/static/uploads/{filename}"
    user.profile_picture_url = file_url

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating profile picture: {e}")
        return jsonify({'error': 'An error occurred while uploading the profile picture'}), 500

    return jsonify({'message': 'Profile picture uploaded successfully', 'profile_picture_url': file_url}), 200