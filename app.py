

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from datetime import datetime

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'baffvdvdzxcdfvv654524vbg54fb4'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newflask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)



@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if password != password_confirm:
            flash('Пароли не совподают!')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, name=name, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except:
            flash('User already exists!')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = (username == ADMIN_USERNAME)
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из аккаунта')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please log in to access your profile.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.name = request.form.get('name') 

        
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if password and password == password_confirm:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            user.password = hashed_password
            flash('Пароль успешно обновлён!')
        elif password and password != password_confirm:
            flash('Пароли не совпадают!')
            return redirect(url_for('profile'))

        db.session.commit()
        flash('Профиль успешно обновлён!')

    return render_template('profile.html', user=user)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(150), nullable=False)
    procedures = db.relationship('Procedure', backref='doctor', lazy=True)

class Procedure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointments = db.relationship('Appointment', backref='procedure', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    procedure_id = db.Column(db.Integer, db.ForeignKey('procedure.id'), nullable=False)
    patient_name = db.Column(db.String(150), nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)


@app.route('/doctors', methods=['POST'])
def create_doctor():
    name = request.form.get('name')
    specialization = request.form.get('specialization')
    new_doctor = Doctor(name=name, specialization=specialization)
    db.session.add(new_doctor)
    db.session.commit()
    return "Doctor created successfully!", 201

ADMIN_USERNAME = "Admin"

@app.route('/doctors', methods=['GET'])
def get_doctors():
    doctors = Doctor.query.all()
    is_admin = 'user_id' in session and User.query.get(session['user_id']).username == ADMIN_USERNAME
    return render_template('doctors.html', doctors=doctors, is_admin=is_admin)


@app.route('/doctors/<int:id>', methods=['PUT'])
def update_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    doctor.name = request.form.get('name')
    doctor.specialization = request.form.get('specialization')
    db.session.commit()
    return "Doctor updated successfully!", 200


@app.route('/doctors/<int:id>/delete', methods=['GET', 'POST'])
def delete_doctor(id):
    if 'user_id' not in session or User.query.get(session['user_id']).username != ADMIN_USERNAME:
        flash('Access denied: Only admin can delete doctors.')
        return redirect(url_for('get_doctors'))

    doctor = Doctor.query.get_or_404(id)

    if request.method == 'POST':
        db.session.delete(doctor)
        db.session.commit()
        flash('Doctor deleted successfully!')
        return redirect(url_for('get_doctors'))

    return render_template('delete_doctor.html', doctor=doctor)


@app.route('/doctors/<int:id>/edit', methods=['GET', 'POST'])
def edit_doctor(id):
    if 'user_id' not in session or User.query.get(session['user_id']).username != ADMIN_USERNAME:
        flash('Access denied: Only admin can edit doctors.')
        return redirect(url_for('get_doctors'))

    doctor = Doctor.query.get_or_404(id)

    if request.method == 'POST':
        doctor.name = request.form.get('name')
        doctor.specialization = request.form.get('specialization')
        db.session.commit()
        flash('Doctor updated successfully!')
        return redirect(url_for('get_doctors'))

    return render_template('edit_doctor.html', doctor=doctor)


@app.route('/procedures', methods=['GET', 'POST'])
def procedures():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        doctor_id = request.form.get('doctor_id')

        new_procedure = Procedure(name=name, price=price, doctor_id=doctor_id)
        db.session.add(new_procedure)
        db.session.commit()
        return redirect(url_for('procedures'))

    procedures_list = Procedure.query.all()
    return render_template('procedures.html', procedures=procedures_list)



@app.route('/appointments', methods=['GET'])
def view_appointments():
    appointments = Appointment.query.all()  
    return render_template('appointments.html', appointments=appointments)


@app.route('/add_appointment', methods=['GET', 'POST'])
def add_appointment():
    if request.method == 'POST':
        procedure_id = request.form.get('procedure_id')
        patient_name = request.form.get('patient_name')
        appointment_time = request.form.get('appointment_time')
        appointment_time = datetime.strptime(appointment_time, '%Y-%m-%dT%H:%M')
        new_appointment = Appointment(
            procedure_id=procedure_id,
            patient_name=patient_name,
            appointment_time=appointment_time
        )
        db.session.add(new_appointment)
        db.session.commit()
        return redirect(url_for('view_appointments'))

    
    procedures = Procedure.query.all()
    return render_template('add_appointment.html', procedures=procedures)


@app.route('/doctors/add', methods=['GET', 'POST'])
def add_doctor():
    if 'user_id' not in session or User.query.get(session['user_id']).username != ADMIN_USERNAME:
        flash('Access denied: Only admin can add doctors.')
        return redirect(url_for('get_doctors'))

    if request.method == 'POST':
        name = request.form.get('name')
        specialization = request.form.get('specialization')

        new_doctor = Doctor(name=name, specialization=specialization)
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor added successfully!')
        return redirect(url_for('get_doctors'))

    return render_template('add_doctor.html')

@app.route('/procedures/add', methods=['GET', 'POST'])
def add_procedure():
    if 'user_id' not in session or User.query.get(session['user_id']).username != ADMIN_USERNAME:
        flash('Access denied: Only admin can add procedures.')
        return redirect(url_for('procedures'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        doctor_id = request.form.get('doctor_id')

        new_procedure = Procedure(name=name, price=price, doctor_id=doctor_id)
        db.session.add(new_procedure)
        db.session.commit()
        flash('Procedure added successfully!')
        return redirect(url_for('procedures'))

    doctors = Doctor.query.all()
    return render_template('add_procedure.html', doctors=doctors)



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/otzyv')
def testimonials():
    return render_template('otzyv.html')

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if 'user_id' not in session:
        flash('Please log in to delete your account.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()

        session.pop('user_id', None)  # Завершаем сессию пользователя
        flash('Your account has been deleted successfully.')
        return redirect(url_for('index'))  # Перенаправляем на главную страницу

    return render_template('delete_account.html', user=user)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)





