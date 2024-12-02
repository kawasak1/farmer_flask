import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '472dff1ca43b534401fe20aef2d624004d4c5e333eeb75f04e6addf5799557b5'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://farmer_market_vek3_user:UgkJaVCQ02vZqVBdOaMSf670MisYR2yd@dpg-ct6o2ttumphs739ienh0-a.oregon-postgres.render.com/farmer_market_vek3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False