import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '472dff1ca43b534401fe20aef2d624004d4c5e333eeb75f04e6addf5799557b5'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:1111@localhost:5432/farmer_market'
    SQLALCHEMY_TRACK_MODIFICATIONS = False