import os
from flask import Flask, jsonify
from config import Config
from extensions import db, migrate, login_manager, bcrypt, api, jwt
from werkzeug.exceptions import RequestEntityTooLarge

# def create_app():
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
bcrypt.init_app(app)
api.init_app(app)
jwt.init_app(app)

# Import models after initializing db to prevent circular imports
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(RequestEntityTooLarge)
def handle_file_size_error(e):
    return jsonify({'error': 'File is too large'}), 413

# Register Blueprints
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.profile_routes import profile_bp
from routes.cart_routes import cart_bp
from routes.order_routes import order_bp
from routes.chat_routes import chat_bp
from routes.offer_routes import offer_bp
app.register_blueprint(auth_bp)
app.register_blueprint(product_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(order_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(offer_bp)

    # return app


# if __name__ == '__main__':
#     app = create_app()
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port)