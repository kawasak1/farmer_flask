from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from app import app


from extensions import db
from models import User, Farmer, Product, Category, ProductImage

from schemas import ProductSchema, UpdateProductSchema

product_bp = Blueprint('product_bp', __name__)

@product_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    data = request.get_json()
    print(data)
    app.logger.error(data)
    schema = ProductSchema()
    errors = schema.validate(data)
    app.logger.error(errors)
    print(errors)
    if errors:
        return jsonify(errors), 400

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'farmer':
        return jsonify({'error': 'Only farmers can create products'}), 403

    farmer = Farmer.query.get(user_id)
    if not farmer:
        return jsonify({'error': 'Farmer profile not found'}), 404

    # Extract data
    name = data['name']
    category_id = data.get('category_id')
    category_name = data.get('category_name')
    description = data.get('description')
    price = data['price']
    quantity_available = data['quantity_available']
    quantity_unit = data['quantity_unit']
    is_active = data.get('is_active', True)
    image_urls = data.get('images', [])

    # Determine Category
    category = None
    if category_id:
        category = Category.query.get(category_id)
        if not category:
            if category_name:
                # Create new category with provided name
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()  # To get category.id
            else:
                return jsonify({'error': f'Category with id {category_id} does not exist. Provide a valid category_id or category_name to create a new category.'}), 400
    elif category_name:
        # Check if category with that name exists
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            # Create new category
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()  # To get category.id
    else:
        return jsonify({'error': 'Either category_id or category_name must be provided.'}), 400

    print(data)
    # Create the Product
    product = Product(
        farmer_id=user_id,
        name=name,
        category_id=category.id,
        description=description,
        price=price,
        quantity_available=quantity_available,
        quantity_unit=quantity_unit,
        is_active=is_active
    )

    db.session.add(product)
    db.session.flush()  # Flush to get product.id before committing

    # Add Product Images
    for idx, image_url in enumerate(image_urls):
        product_image = ProductImage(
            product_id=product.id,
            image_url=image_url,
            order_num=idx + 1
        )
        db.session.add(product_image)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'An error occurred while creating the product'}), 500

    return jsonify({'message': 'Product created successfully', 'product_id': product.id}), 201

@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    data = request.get_json()
    schema = UpdateProductSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify(errors), 400

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role != 'farmer':
        return jsonify({'error': 'Only farmers can update products'}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.farmer_id != user_id:
        return jsonify({'error': 'You do not have permission to update this product'}), 403

    # Update product fields
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = data['price']
    if 'quantity_available' in data:
        product.quantity_available = data['quantity_available']
    if 'quantity_unit' in data:
        product.quantity_unit = data['quantity_unit']
    if 'is_active' in data:
        product.is_active = data['is_active']

    # Handle category update
    category_id = data.get('category_id')
    category_name = data.get('category_name')

    if category_id is not None or category_name is not None:
        # Determine Category
        category = None
        if category_id is not None:
            category = Category.query.get(category_id)
            if not category:
                if category_name:
                    # Create new category with provided name
                    category = Category(name=category_name)
                    db.session.add(category)
                    db.session.flush()  # To get category.id
                else:
                    return jsonify({'error': f'Category with id {category_id} does not exist. Provide a valid category_id or category_name to create a new category.'}), 400
        elif category_name:
            # Check if category with that name exists
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                # Create new category
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()  # To get category.id
        # Update product's category_id
        product.category_id = category.id

    # Update images if provided
    if 'images' in data:
        # Delete existing images
        ProductImage.query.filter_by(product_id=product.id).delete()
        db.session.flush()
        # Add new images
        for idx, image_url in enumerate(data['images']):
            product_image = ProductImage(
                product_id=product.id,
                image_url=image_url,
                order_num=idx + 1
            )
            db.session.add(product_image)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while updating the product'}), 500

    return jsonify({'message': 'Product updated successfully'}), 200

@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role != 'farmer':
        return jsonify({'error': 'Only farmers can delete products'}), 403

    product = Product.query.get(product_id)
    print(product)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.farmer_id != user_id:
        return jsonify({'error': 'You do not have permission to delete this product'}), 403

    try:
        db.session.delete(product)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error deleting product: {e}")
        return jsonify({'error': 'An error occurred while deleting the product'}), 500

    return jsonify({'message': 'Product deleted successfully'}), 200


@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'error': 'Product not found'}), 404

    product_data = {
        'id': product.id,
        'name': product.name,
        'category': product.category.name if product.category else None,
        'description': product.description,
        'price': str(product.price),
        'quantity_available': product.quantity_available,
        'quantity_unit': product.quantity_unit,
        'farmer_id': product.farmer_id,
        'farmer_name': product.farmer.user.first_name + ' ' + product.farmer.user.last_name,
        'images': [img.image_url for img in product.images.order_by(ProductImage.order_num).all()],
        'created_at': product.created_at.isoformat(),
        'updated_at': product.updated_at.isoformat()
    }

    return jsonify(product_data), 200

@product_bp.route('/products/farmer', methods=['GET'])
@jwt_required()
def get_my_products():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'farmer':
        return jsonify({'error': 'Only farmers can access their own products'}), 403

    products = Product.query.filter_by(farmer_id=user_id).all()

    results = []
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else None,
            'description': product.description,
            'price': str(product.price),
            'quantity_available': product.quantity_available,
            'quantity_unit': product.quantity_unit,
            'is_active': product.is_active,
            'images': [img.image_url for img in product.images.order_by(ProductImage.order_num).all()],
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat()
        }
        results.append(product_data)

    return jsonify({'products': results}), 200

@product_bp.route('/products', methods=['GET'])
def list_products():
    # Build query
    query = Product.query

    products = query

    results = []
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category.name if product.category else None,
            'price': str(product.price),
            'quantity_available': product.quantity_available,
            'quantity_unit': product.quantity_unit,
            'farmer_name': product.farmer.user.first_name + ' ' + product.farmer.user.last_name,
            'images': [img.image_url for img in product.images.order_by(ProductImage.order_num).all()],
            'created_at': product.created_at.isoformat(),
        }
        results.append(product_data)

    response = {
        'products': results,
    }

    return jsonify(response), 200

@product_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    category_list = [{'id': cat.id, 'name': cat.name, 'description': cat.description} for cat in categories]
    return jsonify({'categories': category_list}), 200