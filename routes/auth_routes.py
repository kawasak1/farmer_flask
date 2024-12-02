from flask import Blueprint, request, jsonify
from flask_login import login_user
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity,
)
from datetime import timedelta
from extensions import db, bcrypt
from models import User, Farmer, Buyer

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register_farmer', methods=['POST'])
def register_farmer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    # Extract and validate data
    required_fields = ['email', 'password', 'first_name', 'last_name', 'farm_name']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    email = data['email']
    password = data['password']
    first_name = data['first_name']
    last_name = data['last_name']
    username = data.get('username')
    phone_number = data.get('phone_number')
    farm_name = data['farm_name']
    farm_size = data.get('farm_size')
    farm_address = data.get('farm_address')
    farm_description = data.get('farm_description')
    crops_grown = data.get('crops_grown')  # Should be a list or string

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered'}), 409
    if username and User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username is already taken'}), 409

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create the User object
    user = User(
        email=email,
        username=username,
        password_hash=hashed_password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role='farmer',
        is_active=True  # Or False if you require email verification
    )
    db.session.add(user)
    db.session.commit()

    # Create the Farmer object
    farmer = Farmer(
        user_id=user.id,
        farm_name=farm_name,
        farm_size=farm_size,
        farm_address=farm_address,
        farm_description=farm_description,
        crops_grown=crops_grown
    )
    db.session.add(farmer)
    db.session.commit()

    # Generate JWT tokens
    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
    refresh_token = create_refresh_token(identity=user.id, expires_delta=timedelta(days=3))

    return jsonify({'message': 'Farmer registered successfully','access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.id}), 201

@auth_bp.route('/register_buyer', methods=['POST'])
def register_buyer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    # Extract and validate data
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    email = data['email']
    password = data['password']
    first_name = data['first_name']
    last_name = data['last_name']
    username = data.get('username')
    phone_number = data.get('phone_number')
    default_delivery_address = data.get('default_delivery_address')
    preferred_payment_method = data.get('preferred_payment_method')

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered'}), 409
    if username and User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username is already taken'}), 409

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create the User object
    user = User(
        email=email,
        username=username,
        password_hash=hashed_password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role='buyer',
        is_active=True  # Or False if you require email verification
    )
    db.session.add(user)
    db.session.commit()

    # Create the Buyer object
    buyer = Buyer(
        user_id=user.id,
        default_delivery_address=default_delivery_address,
        preferred_payment_method=preferred_payment_method
    )
    db.session.add(buyer)
    db.session.commit()

    # Generate JWT tokens
    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
    refresh_token = create_refresh_token(identity=user.id, expires_delta=timedelta(days=3))

    return jsonify({'message': 'Buyer registered successfully', 'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    email_or_username = data.get('email_or_username')
    password = data.get('password')

    if not email_or_username or not password:
        return jsonify({'error': 'Email/username and password are required'}), 400

    # Find user by email or username
    user = User.query.filter(
        (User.email == email_or_username) | (User.username == email_or_username)
    ).first()

    print(user)

    if user and bcrypt.check_password_hash(user.password_hash, password):
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        login_user(user)

        # Generate JWT tokens
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
        refresh_token = create_refresh_token(identity=user.id, expires_delta=timedelta(days=3))

        # Return user info (excluding sensitive data)
        user_data = {
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        }

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_data
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401