from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "secret-key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- LOGIN ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

# ---------------- MODEL ----------------
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    ward = db.Column(db.String(50))
    doctor = db.Column(db.String(100))
    fees = db.Column(db.Float)

# ---------------- USERS ----------------
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id, users[user_id]["role"])
    return None

with app.app_context():
    db.create_all()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("home.html")

# ---------------- LOGIN PAGE ----------------
@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users.get(data['username'])

    if user and user['password'] == data['password']:
        u = User(data['username'], user['role'])
        login_user(u)
        return jsonify({"role": user["role"]})

    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("admin.html" if current_user.role == "admin" else "user.html")

# ---------------- PATIENTS ----------------
@app.route('/patients', methods=['GET'])
@login_required
def get_patients():
    patients = Patient.query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "ward": p.ward,
            "doctor": p.doctor,
            "fees": p.fees
        }
        for p in patients
    ])

@app.route('/patients', methods=['POST'])
@login_required
def add_patient():
    if current_user.role != "admin":
        return jsonify({"message": "Access denied"}), 403

    data = request.json

    p = Patient(
        name=data['name'],
        age=data['age'],
        ward=data['ward'],
        doctor=data['doctor'],
        fees=data['fees']
    )

    db.session.add(p)
    db.session.commit()

    return jsonify({"message": "Patient added"})

@app.route('/patients/<int:id>', methods=['DELETE'])
@login_required
def delete_patient(id):
    if current_user.role != "admin":
        return jsonify({"message": "Access denied"}), 403

    p = Patient.query.get(id)
    db.session.delete(p)
    db.session.commit()

    return jsonify({"message": "Deleted"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)