from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from barcode import EAN13
from barcode.writer import ImageWriter
import os

app = Flask(__name__)

# Config for SQLAlchemy and Flask-Mail
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:compound#1@localhost:5432/barcode_mebal'  # PostgreSQL connection URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'info@mebal.ca'  # email address
app.config['MAIL_PASSWORD'] = 'Comeng123)(*'  # email password

db = SQLAlchemy(app)
mail = Mail(app)

class Registration(db.Model):
    id = db.Column(db.String, primary_key=True)
    barcode = db.Column(db.String)
    email = db.Column(db.String)
    servings = db.Column(db.Integer)

@app.route('/register', methods=['POST'])
def register():
    attendee_info = request.json

    barcode = EAN13(attendee_info['id'], writer=ImageWriter())
    barcode_path = f"barcodes/{attendee_info['id']}.png"
    barcode.save(barcode_path)

    registration = Registration(id=attendee_info['id'], barcode=barcode.get_fullcode(), email=attendee_info['email'], servings=attendee_info['attendees'])
    db.session.add(registration)
    db.session.commit()

    msg = Message('Successful Registration', sender='info@mebal.ca', recipients=[attendee_info['email']])
    msg.body = f"Hello, you've successfully registered for the MEBAL Summer Beach Party on Saturday July 22, 2023. Your barcode is {barcode.get_fullcode()}. You have {attendee_info['attendees']} servings."
    with app.open_resource(barcode_path) as fp:
        msg.attach("barcode.png", "image/png", fp.read())
    mail.send(msg)

    os.remove(barcode_path)  # Remove the barcode image after sending the email

    return jsonify(message="Registration successful!"), 200

@app.route('/validate', methods=['POST'])
def validate():
    barcode = request.json['barcode']

    registration = Registration.query.filter_by(barcode=barcode).first()

    if registration:
        if registration.servings > 0:
            registration.servings -= 1
            db.session.commit()
            return jsonify(message="Catering served!", remaining_servings=registration.servings), 200
        else:
            return jsonify(message="No remaining servings for this participant."), 200

    return jsonify(message="Invalid barcode."), 400

if __name__ == "__main__":
    app.run(debug=True)
