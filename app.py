from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# Step 1: Create app
app = Flask(__name__)

# Step 2: Configure database (ADD HERE)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Step 3: Initialize DB (ADD HERE)
db = SQLAlchemy(app)

# Step 4: Create Model (ADD HERE)
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# Step 5: Routes
@app.route('/')
def home():
    return "CI/CD Pipeline Working!"

@app.route('/cars', methods=['GET'])
def get_cars():
    cars = Car.query.all()
    return jsonify([{"id": c.id, "name": c.name} for c in cars])

@app.route('/cars', methods=['POST'])
def add_car():
    data = request.json
    new_car = Car(name=data['name'])
    db.session.add(new_car)
    db.session.commit()
    return jsonify({"message": "Car added"})

# Step 6: Run app
if __name__ == '__main__':
    # Create DB tables automatically
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)