from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from barcode import EAN13
from barcode.writer import ImageWriter
import os

app = Flask(__name__)

# Config for SQLAlchemy and SendGrid
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:compound#1@localhost:5432/barcode_mebal'
#app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('postgresql://postgres:compound#1@localhost:5432/barcode_mebal')  # replace with your Postgres DB URL
#app.config['SENDGRID_API_KEY'] = os.getenv('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')  # replace with your SendGrid API key
app.config['SENDGRID_API_KEY'] = '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'

db = SQLAlchemy(app)
with app.app_context():
    db.create_all() 

class Registration(db.Model):
    id = db.Column(db.String, primary_key=True)
    barcode = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    servings = db.Column(db.Integer)

@app.route('/register', methods=['POST'])
def register():
    attendee_info = request.json

    if Registration.query.filter_by(id=attendee_info['id']).first():
        return jsonify(message="This ID is already registered."), 400

    if Registration.query.filter_by(email=attendee_info['email']).first():
        return jsonify(message="This email is already registered."), 400

    barcode = EAN13(attendee_info['id'], writer=ImageWriter())
    barcode.save(f"barcode_{attendee_info['id']}")

    registration = Registration(id=attendee_info['id'], barcode=barcode.get_fullcode(), email=attendee_info['email'], servings=attendee_info['attendees'])
    db.session.add(registration)
    db.session.commit()

    message = Mail(
        from_email='YOUR_EMAIL',  # replace with your email
        to_emails=attendee_info['email'],
        subject='Successful Registration',
        html_content=f"<p>Hello, you've successfully registered for the MEBAL Summer Beach Party on Saturday July 22, 2023. Your barcode is {barcode.get_fullcode()}. You have {attendee_info['attendees']} servings.</p><p><img src='cid:barcode'></p>"
    )
    with open(f"barcode_{attendee_info['id']}.png", 'rb') as fp:
        message.add_attachment(fp.read(), 'image/png', 'barcode', 'inline', 'barcode')
    try:
        sg = SendGridAPIClient(app.config['SENDGRID_API_KEY'])
        sg.send(message)
    except Exception as e:
        print(str(e))

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
    db.create_all()  # create database tables
    app.run(debug=True)
