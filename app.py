from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "secret-key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

# -------- MODELS --------
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    doctor = db.Column(db.String(100))

class LabRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer)
    test = db.Column(db.String(100))
    result = db.Column(db.String(200))

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer)
    medicine = db.Column(db.String(100))
    quantity = db.Column(db.Integer)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    stock = db.Column(db.Integer)
    price = db.Column(db.Float)

# -------- USERS --------
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "doctor": {"password": "doc123", "role": "doctor"},
    "lab": {"password": "lab123", "role": "lab"},
    "pharma": {"password": "pharma123", "role": "pharmacy"},
    "patient": {"password": "patient123", "role": "patient"}
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

LAB_TESTS = ["X-Ray", "Blood Test", "MRI", "CT Scan"]

# -------- ROUTES --------
@app.route('/')
def home():
    return render_template("home.html")

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users.get(data['username'])

    if user and user['password'] == data['password']:
        login_user(User(data['username'], user['role']))
        return jsonify({"msg": "ok"})

    return jsonify({"msg": "Invalid"}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template(f"{current_user.role}.html")

# -------- ADMIN --------
@app.route('/add_patient', methods=['POST'])
@login_required
def add_patient():
    if current_user.role != "admin":
        return "Unauthorized", 403

    d = request.json
    db.session.add(Patient(name=d['name'], age=d['age'], doctor=d['doctor']))
    db.session.commit()
    return "Added"

@app.route('/patients')
@login_required
def patients():
    p = Patient.query.all()
    return jsonify([{"id":x.id,"name":x.name,"age":x.age,"doctor":x.doctor} for x in p])

@app.route('/delete_patient/<int:id>', methods=['DELETE'])
@login_required
def delete_patient(id):
    if current_user.role != "admin":
        return "Unauthorized", 403

    db.session.delete(Patient.query.get(id))
    db.session.commit()
    return "Deleted"

# -------- DOCTOR --------
@app.route('/patient/<int:id>')
@login_required
def patient_detail(id):
    if current_user.role != "doctor":
        return "Unauthorized", 403

    p = Patient.query.get(id)
    return render_template("patient_form.html", patient=p, tests=LAB_TESTS)

@app.route('/prescribe', methods=['POST'])
@login_required
def prescribe():
    if current_user.role != "doctor":
        return "Unauthorized", 403

    d = request.json

    db.session.add(Prescription(
        patient_id=d['patient_id'],
        medicine=d['medicine'],
        quantity=d['qty']
    ))

    if d['test'] != "":
        db.session.add(LabRequest(
            patient_id=d['patient_id'],
            test=d['test'],
            result="Pending"
        ))

    db.session.commit()
    return "Saved"

# -------- LAB --------
@app.route('/lab')
@login_required
def lab():
    return jsonify([{
        "id":l.id,
        "patient_id":l.patient_id,
        "test":l.test,
        "result":l.result
    } for l in LabRequest.query.all()])

@app.route('/lab_update', methods=['POST'])
@login_required
def lab_update():
    if current_user.role != "lab":
        return "Unauthorized", 403

    d = request.json
    lr = LabRequest.query.get(d['id'])
    lr.result = d['result']
    db.session.commit()
    return "Updated"

# -------- PHARMACY --------
@app.route('/add_med', methods=['POST'])
@login_required
def add_med():
    if current_user.role != "pharmacy":
        return "Unauthorized", 403

    d = request.json
    db.session.add(Medicine(name=d['name'], stock=d['stock'], price=d['price']))
    db.session.commit()
    return "Added"

@app.route('/meds')
@login_required
def meds():
    return jsonify([{
        "id":m.id,
        "name":m.name,
        "stock":m.stock,
        "price":m.price
    } for m in Medicine.query.all()])

# -------- PATIENT --------
@app.route('/my')
@login_required
def my():
    if current_user.role != "patient":
        return "Unauthorized", 403

    p = Patient.query.first()

    return jsonify({
        "patient": p.name,
        "labs": [l.test + " - " + l.result for l in LabRequest.query.filter_by(patient_id=p.id)],
        "pres": [pr.medicine for pr in Prescription.query.filter_by(patient_id=p.id)]
    })

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)