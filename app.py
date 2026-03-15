from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(200))

class Medicine(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    dosage = db.Column(db.String(100))
    stock = db.Column(db.Integer)
    user_id = db.Column(db.Integer)

class Reminder(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer)
    reminder_time = db.Column(db.String(10))

class History(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(100))
    taken_time = db.Column(db.String(100))
    user_id = db.Column(db.Integer)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        user = User(username=username,email=email,password=password)

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password,password):

            login_user(user)

            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():

    medicines = Medicine.query.filter_by(user_id=current_user.id).all()

    reminder_map = {}

    for med in medicines:
        reminders = Reminder.query.filter_by(medicine_id=med.id).all()
        reminder_map[med.id] = reminders

    return render_template(
        'dashboard.html',
        medicines=medicines,
        reminder_map=reminder_map
    )

@app.route('/add', methods=['GET','POST'])
@login_required
def add():

    if request.method == 'POST':

        name = request.form['name']
        dosage = request.form['dosage']
        stock = int(request.form['stock'])

        medicine = Medicine(
            name=name,
            dosage=dosage,
            stock=stock,
            user_id=current_user.id
        )

        db.session.add(medicine)
        db.session.commit()

        reminders = request.form.getlist('reminder')

        for r in reminders:

            if r != "":
                rem = Reminder(
                    medicine_id=medicine.id,
                    reminder_time=r
                )

                db.session.add(rem)

        db.session.commit()

        return redirect('/dashboard')

    return render_template('add_medicine.html')

@app.route('/taken/<int:id>')
@login_required
def taken(id):

    medicine = db.session.get(Medicine, id)

    if medicine.stock > 0:
        medicine.stock -= 1

    current_time = datetime.now()

    history = History(
        medicine_name=medicine.name,
        taken_time=datetime.now().strftime("%d %b %Y  %I:%M %p"),
        user_id=current_user.id
    )

    db.session.add(history)

    if medicine.stock <= 0:

        Reminder.query.filter_by(medicine_id=id).delete()
        db.session.delete(medicine)

    db.session.commit()

    return redirect('/dashboard')

@app.route('/delete/<int:id>')
@login_required
def delete(id):

    medicine = db.session.get(Medicine,id)

    Reminder.query.filter_by(medicine_id=id).delete()

    db.session.delete(medicine)

    db.session.commit()

    return redirect('/dashboard')

@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):

    medicine = db.session.get(Medicine, id)

    if request.method == 'POST':

        medicine.name = request.form['name']
        medicine.dosage = request.form['dosage']
        medicine.stock = int(request.form['stock'])

        Reminder.query.filter_by(medicine_id=id).delete()

        reminder_times = request.form.getlist('reminder')

        for time in reminder_times:

            if time != "":
                new_reminder = Reminder(
                    medicine_id=id,
                    reminder_time=time
                )

                db.session.add(new_reminder)

        db.session.commit()

        return redirect('/dashboard')

    reminders = Reminder.query.filter_by(medicine_id=id).all()

    return render_template(
        'edit_medicine.html',
        medicine=medicine,
        reminders=reminders
    )

@app.route('/history')
@login_required
def history():

    history = History.query.filter_by(user_id=current_user.id).order_by(History.id.desc()).all()

    return render_template('history.html',history=history)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
