from marshmallow import Schema, fields, validate

class ProductSchema(Schema):
    name = fields.Str(required=True)
    category_id = fields.Integer(required=False)
    category_name = fields.String(required=False)
    description = fields.Str()
    price = fields.Decimal(as_string=True, required=True)
    quantity_available = fields.Int(required=True)
    quantity_unit = fields.Str(required=True)
    is_active = fields.Boolean()
    images = fields.List(fields.Url())

class UpdateProductSchema(Schema):
    name = fields.String(required=False)
    category_id = fields.Integer(required=False)
    category_name = fields.String(required=False)
    description = fields.String(required=False)
    price = fields.Float(required=False)
    quantity_available = fields.Integer(required=False)
    quantity_unit = fields.String(required=False)
    is_active = fields.Boolean(required=False)
    images = fields.List(fields.String(), required=False)

class UserProfileSchema(Schema):
    email = fields.Email(required=True)
    username = fields.String(required=False)
    first_name = fields.String(required=False)
    last_name = fields.String(required=False)
    phone_number = fields.String(required=False)
    profile_picture_url = fields.String(required=False)
    role = fields.String(required=True)

class UpdateUserProfileSchema(Schema):
    username = fields.String(required=False)
    first_name = fields.String(required=False)
    last_name = fields.String(required=False)
    phone_number = fields.String(required=False)
    profile_picture_url = fields.Url(required=False)

# Farmer Profile Schemas
class FarmerProfileSchema(Schema):
    user = fields.Nested(UserProfileSchema)
    farm_name = fields.String(required=False)
    farm_size = fields.Float(required=False)
    farm_address = fields.String(required=False)
    farm_description = fields.String(required=False)
    crops_grown = fields.String(required=False)

class UpdateFarmerProfileSchema(Schema):
    farm_name = fields.String(required=False)
    farm_size = fields.Float(required=False)
    farm_address = fields.String(required=False)
    farm_description = fields.String(required=False)
    crops_grown = fields.String(required=False)

# Buyer Profile Schemas
class BuyerProfileSchema(Schema):
    user = fields.Nested(UserProfileSchema)
    default_delivery_address = fields.String(required=False)
    preferred_payment_method = fields.String(required=False)

class UpdateBuyerProfileSchema(Schema):
    default_delivery_address = fields.String(required=False)
    preferred_payment_method = fields.String(required=False)