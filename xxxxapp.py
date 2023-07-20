from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from barcode import EAN13
from barcode.writer import ImageWriter

app = Flask(__name__)

# Config for SQLAlchemy and Flask-Mail
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # Replace with your actual database connection string
app.config['MAIL_SERVER'] = 'smtp.example.com'  # Replace with your actual mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'YOUR_EMAIL'  # Replace with your actual email
app.config['MAIL_PASSWORD'] = 'YOUR_PASSWORD'  # Replace with your actual password

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

    existing_registration = Registration.query.filter_by(email=attendee_info['email']).first()
    if existing_registration:
        return jsonify(message="You have already registered."), 400

    barcode = EAN13(attendee_info['id'], writer=ImageWriter())
    barcode.save(f"barcode_{attendee_info['id']}")

    registration = Registration(id=attendee_info['id'], barcode=barcode.get_fullcode(),
                                email=attendee_info['email'], servings=attendee_info['attendees'])
    db.session.add(registration)
    db.session.commit()

    send_registration_email(attendee_info['email'], barcode.get_fullcode(), attendee_info['attendees'])

    return jsonify(message="Registration successful!"), 200


def send_registration_email(recipient, barcode, servings):
    with app.open_resource(f"barcode_{barcode}.png") as fp:
        msg = Message('Successful Registration', sender='YOUR_EMAIL', recipients=[recipient])
        msg.body = f"Hello, you've successfully registered for the event. Your barcode is {barcode}. " \
                   f"You have {servings} servings."
        msg.attach("barcode.png", "image/png", fp.read())
        mail.send(msg)


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
    # Set your production-ready configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your_production_db_connection_string'
    app.config['MAIL_SERVER'] = 'your_production_mail_server'
    app.config['MAIL_USERNAME'] = 'your_production_email'
    app.config['MAIL_PASSWORD'] = 'your_production_password'

    db.create_all()  # Create database tables

    app.run(debug=False)  # Set debug=False for production


