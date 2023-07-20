from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from barcode import EAN13
from barcode.writer import ImageWriter
import base64

app = Flask(__name__)

# Config for SQLAlchemy and Flask-Mail
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://ipydhizqihcdqg:59e5a4d67cff256f629318c199ee91c94230d0295ed8886d5d10faca8e569b54@ec2-52-205-45-222.compute-1.amazonaws.com:5432/d837b9p05cajih'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # your mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'info@mebal.ca'  # your username
app.config['MAIL_PASSWORD'] = 'Comeng123)(*'  # your password

db = SQLAlchemy(app)
mail = Mail(app)

class Registration(db.Model):
    id = db.Column(db.String, primary_key=True)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    barcode = db.Column(db.String)
    email = db.Column(db.String)
    servings = db.Column(db.Integer)

@app.route('/', methods=['GET'])
def mebal():
    return jsonify(message='Hello world'), 200



@app.route('/register', methods=['POST'])
def register():
    attendee_info = request.json

    barcode = EAN13(attendee_info['id'].zfill(12), writer=ImageWriter())
    barcode.save(f"barcode_{attendee_info['id']}")

    registration = Registration(id=attendee_info['id'], barcode=barcode.get_fullcode(), email=attendee_info['email'], servings=attendee_info['attendees'])
    db.session.add(registration)
    db.session.commit()

    msg = Message('MEBAL Summer Beach Party', sender='info@mebal.ca', recipients=[attendee_info['email']])
    msg.body = f"Hello, you've successfully registered your attendance for the MEBAL Summer Beach Party on Saturday July 22, 2023. Your barcode is {barcode.get_fullcode()}. You have {attendee_info['attendees']} servings."
    with app.open_resource(f"barcode_{attendee_info['id']}.png") as fp:
        msg.attach("barcode.png", "image/png", fp.read())
    mail.send(msg)

    return jsonify(message="Registration successful!"), 200

@app.route('/validate', methods=['POST'])
def validate():
    barcode = request.json['barcode']

    registration = Registration.query.filter_by(barcode=barcode).first()

    if registration:
        if registration.servings > 0:
            registration.servings -= 1
            db.session.commit()
            return jsonify(message="Catering served! Please enjoy", remaining_servings=registration.servings), 200
        else:
            return jsonify(message="No remaining servings for this guest."), 200

    return jsonify(message="Invalid barcode."), 400

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # create database tables
    app.run(debug=True)