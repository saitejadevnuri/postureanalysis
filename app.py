from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import posture_analysis  # Import the posture analysis module

from globals import warnings_sent
# Flask application setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

# Twilio configuration

# Database models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    age = db.Column(db.Integer, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    phone_number = request.form['phone_number']
    age = int(request.form['age'])

    if User.query.filter_by(username=username).first():
        flash('Username already exists.')
        return redirect(url_for('index'))

    new_user = User(username=username, password=password, phone_number=phone_number, age=age)
    db.session.add(new_user)
    db.session.commit()

    flash('Registration successful. Please log in.')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()

    if user:
        login_user(user)
        flash('Login successful.')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password.')
    
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/video_feed')
@login_required
def video_feed():
    # Pass the current user's phone number to posture analysis
    return Response(gen_video_feed(current_user.phone_number), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_video_feed(phone_number):
    # Streaming video feed from posture analysis
    for frame in posture_analysis.process_frame(phone_number):
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
# Route to reset the warning flag
@app.route('/reset_warnings', methods=['POST'])
@login_required
def reset_warnings():
    warnings_sent[current_user.phone_number] = False
    flash('Warning has been reset. You can receive warnings again.')
    return redirect(url_for('dashboard'))
# Initialize as False (no warning sent yet)


if __name__ == '__main__':
    # Ensure the tables are created in the database
    with app.app_context():
        db.create_all()  # This will create the tables in the database

    app.run(debug=True)

