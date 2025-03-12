from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from datetime import timedelta
from models import db, User, Equipment  # Import models

app = Flask(__name__)
CORS(app)

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:youtheone06@localhost/rental_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db.init_app(app)
jwt = JWTManager(app)

# Drop and recreate tables
with app.app_context():
    db.drop_all()  # Deletes all existing tables
    db.create_all()  # Recreates tables

@app.route('/')
def home():
    return "Rental Equipment System API is running!"

# User Registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    user = User(email=data['email'], password=data['password'], role=data.get('role', 'user'))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered"}), 201

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email'], password=data['password']).first()
    if user:
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return jsonify({"token": token, "role": user.role})
    return jsonify({"error": "Invalid credentials"}), 401

# Add Equipment (Admin Only)
@app.route('/api/equipment', methods=['POST'])
@jwt_required()
def add_equipment():
    if get_jwt().get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    equipment = Equipment(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        available=data.get('available', True)
    )
    db.session.add(equipment)
    db.session.commit()
    return jsonify({"message": "Equipment added"}), 201

# Get All Equipment
@app.route('/api/equipment', methods=['GET'])
def get_equipment():
    equipment = Equipment.query.all()
    return jsonify([{
        "id": e.id,
        "name": e.name,
        "description": e.description,
        "price": e.price,
        "available": e.available
    } for e in equipment])

# Update Equipment (Admin Only)
@app.route('/api/equipment/<int:equip_id>', methods=['PUT'])
@jwt_required()
def update_equipment(equip_id):
    if get_jwt().get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    equipment = Equipment.query.get(equip_id)
    if equipment:
        data = request.get_json()
        equipment.name = data.get("name", equipment.name)
        equipment.description = data.get("description", equipment.description)
        equipment.price = data.get("price", equipment.price)
        equipment.available = data.get("available", equipment.available)
        db.session.commit()
        return jsonify({"message": "Equipment updated"})
    return jsonify({"error": "Equipment not found"}), 404

# Delete Equipment (Admin Only)
@app.route('/api/equipment/<int:equip_id>', methods=['DELETE'])
@jwt_required()
def delete_equipment(equip_id):
    if get_jwt().get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    equipment = Equipment.query.get(equip_id)
    if equipment:
        db.session.delete(equipment)
        db.session.commit()
        return jsonify({"message": "Equipment deleted"})
    return jsonify({"error": "Equipment not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
