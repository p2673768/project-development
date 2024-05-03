from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, RadioField, SelectField, DateTimeField, DateTimeLocalField, IntegerField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, EqualTo, NumberRange
from wtforms_components import DateField
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask import flash
from flask import abort
from flask import session

app = Flask(__name__)   #declares as an application file
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True

db = SQLAlchemy(app)     #declares SQLAlchemy as database

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin): #db model for the user
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    bmi = db.Column(db.Float)
    bmi_date = db.Column(db.DateTime)
    tdee = db.Column(db.Float)
    tdee_date = db.Column(db.DateTime)
    food_log = db.relationship('FoodLog', backref='user', lazy=True)
    workout_log = db.relationship('WorkoutLog', backref='user', lazy=True)

class FoodLog(db.Model): #db model for the food log 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    log_date = db.Column(db.DateTime, default=datetime.utcnow)
    

class WorkoutLog(db.Model): #db model for the workout log
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    intensity = db.Column(db.String(50), nullable=False)
    log_date = db.Column(db.DateTime, default=datetime.utcnow)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                "That username already exists. Please choose a different one.")
        
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

class BmiForm(FlaskForm):
    weight = FloatField('Weight (in kg)', validators=[DataRequired()])
    height = FloatField('Height (in cm)', validators=[DataRequired()])
    submit = SubmitField('Calculate BMI')

class TdeeForm(FlaskForm):
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    weight = FloatField('Weight (in kg)', validators=[DataRequired()])
    height = FloatField('Height (in cm)', validators=[DataRequired()])
    age = FloatField('Age (in years)', validators=[DataRequired()])
    activity_level = SelectField('Activity Level', choices=[('sedentary', 'Sedentary'), ('lightly_active', 'Lightly Active'), ('moderately_active', 'Moderately Active'), ('very_active', 'Very Active')], validators=[DataRequired()])
    submit = SubmitField('Calculate TDEE')

class FoodLogForm(FlaskForm):
    food_name = StringField('Food Name', validators=[DataRequired()])
    quantity = FloatField('Quantity (in grams)', validators=[DataRequired()])
    calories = FloatField('Calories', validators=[DataRequired()])
    protein = FloatField('Protein (in grams)', validators=[DataRequired()])
    carbs = FloatField('Carbs (in grams)', validators=[DataRequired()])
    fats = FloatField('Fats (in grams)', validators=[DataRequired()])
    log_date = DateTimeField('Log Date', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    submit = SubmitField('Log Food')

class WorkoutLogForm(FlaskForm):
    exercise_name = StringField('Exercise Name', validators=[DataRequired()], render_kw={"placeholder": "E.g., Running"})
    intensity = SelectField('Intensity Level',
                            choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')],
                            validators=[DataRequired()],
                            render_kw={"placeholder": "Select Intensity"})
    duration = FloatField('Duration (in minutes)', validators=[DataRequired()], render_kw={"placeholder": "Duration in minutes"})
    # using datetime here to store dates
    log_date = DateTimeLocalField('Log Date and Time',
                                  format='%Y-%m-%dT%H:%M',
                                  validators=[DataRequired()],
                                  render_kw={"placeholder": "YYYY-MM-DDTHH:MM"})
    submit = SubmitField('Log Workout')

class WorkoutPreferenceForm(FlaskForm):   #development of this was abandoned as i wanted to make something more complex (Personal Assessment feature)
    preference = RadioField('Choose your workout focus',
                            choices=[('weight', 'Weight Intensive'),
                                     ('cardio', 'Cardio Intensive'),
                                     ('hybrid', 'Hybrid')],
                            validators=[DataRequired()])
    submit = SubmitField('Next')

class WorkoutDaysForm(FlaskForm):
    days = RadioField('How many days do you want to train?',
                      choices=[('3', '3 Day Split'),
                               ('4', '4 Day Split'),
                               ('5', '5 Day Split')],
                      validators=[DataRequired()])
    submit = SubmitField('Show Plans')

class WorkoutPlanForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=18, max=100)])
    current_weight = FloatField('Current Weight (kg)', validators=[DataRequired(), NumberRange(min=30)])
    goal_weight = FloatField('Goal Weight (kg)', validators=[DataRequired(), NumberRange(min=30)])
    training_preference = RadioField('Training Preference', choices=[
        ('weight', 'Weight Intensive'),
        ('cardio', 'Cardio Intensive'),
        ('hybrid', 'Hybrid (Balanced)')
    ], validators=[DataRequired()])
    submit = SubmitField('Get your results')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods= ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    food_logs = FoodLog.query.filter_by(user_id=current_user.id).all()
    workout_logs = WorkoutLog.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', food_logs=food_logs, workout_logs=workout_logs)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/bmi_calculator', methods=['GET', 'POST'])  #route function for BMI
@login_required
def bmi_calculator():
    form = BmiForm()
    bmi_result = None
    if form.validate_on_submit():
        weight = form.weight.data
        height = form.height.data
        bmi = weight / ((height / 100) ** 2)
        current_user.bmi = bmi
        current_user.bmi_date = datetime.utcnow()
        db.session.commit()
        bmi_result = bmi
        
    return render_template('bmi_calculator.html', title='BMI', form=form, bmi_result=bmi_result)

@app.route('/tdee_calculator', methods=['GET', 'POST'])
@login_required
def tdee_calculator():
    form = TdeeForm()
    tdee_result = None
    if form.validate_on_submit():
        gender = form.gender.data
        weight = form.weight.data
        height = form.height.data
        age = form.age.data
        activity_level = form.activity_level.data
        tdee = calculate_tdee(gender, height, weight, age, activity_level)
        current_user.tdee = tdee
        current_user.tdee_date = datetime.utcnow()
        db.session.commit()
        tdee_result = tdee      
    return render_template('tdee_calculator.html', title='TDEE', form=form, tdee_result=tdee_result)


# Route for viewing food log
@app.route('/food_log', methods=['GET', 'POST'])
@login_required
def food_log():
    form = FoodLogForm()
    if form.validate_on_submit():       
        new_food_log = FoodLog(
            user_id=current_user.id,
            food_name=form.food_name.data,
            quantity=form.quantity.data,
            calories=form.calories.data,
            protein=form.protein.data,
            carbs=form.carbs.data,
            fats=form.fats.data,
            log_date=form.log_date.data
        )
        db.session.add(new_food_log)
        db.session.commit()
        
        return redirect(url_for('dashboard'))         #removed flash messages as they were showing up in login page
    return render_template('food_log.html', form=form)


# route for deleting food log entry
@app.route('/food_log_history')
@login_required
def food_log_history():
    food_logs = FoodLog.query.filter_by(user_id=current_user.id).order_by(FoodLog.log_date.desc()).all()
    return render_template('food_log_history.html', food_logs=food_logs)

# editing food log
@app.route('/edit_food_log/<int:food_log_id>', methods=['GET', 'POST'])
@login_required
def edit_food_log(food_log_id):
    food_log = FoodLog.query.get_or_404(food_log_id)
    if food_log.user_id != current_user.id:
        abort(403)
    form = FoodLogForm()
    if form.validate_on_submit():
        food_log.food_name = form.food_name.data
        food_log.quantity = form.quantity.data
        food_log.calories = form.calories.data
        food_log.protein = form.protein.data
        food_log.carbs = form.carbs.data
        food_log.fats = form.fats.data
        db.session.commit()
        flash('Your food log has been updated!', 'success')
        return redirect(url_for('food_log_history'))
    elif request.method == 'GET':
        form.food_name.data = food_log.food_name
        form.quantity.data = food_log.quantity
        form.calories.data = food_log.calories
        form.protein.data = food_log.protein
        form.carbs.data = food_log.carbs
        form.fats.data = food_log.fats
    return render_template('edit_food_log.html', title='Edit Food Log', form=form)

@app.route('/delete_food_log/<int:food_log_id>', methods=['POST'])  #route for deleting workout entry (working)
@login_required
def delete_food_log(food_log_id):
    food_log = FoodLog.query.get_or_404(food_log_id)
    if food_log.user_id != current_user.id:
        abort(403)
    db.session.delete(food_log)
    db.session.commit()   
    return redirect(url_for('food_log_history'))

# route for viewing workout log
@app.route('/workout_log', methods=['GET', 'POST'])
@login_required
def workout_log():
    form = WorkoutLogForm()
    if form.validate_on_submit():
        new_workout = WorkoutLog(user_id=current_user.id,
                                 exercise_name=form.exercise_name.data,
                                 intensity=form.intensity.data,
                                 duration=form.duration.data,
                                 log_date=form.log_date.data)
        db.session.add(new_workout)
        db.session.commit()        
        return redirect(url_for('dashboard'))
    return render_template('workout_log.html', form=form)


# Route for deleting workout log entry
@app.route('/delete_workout/<int:workout_id>', methods=['POST'])
@login_required
def delete_workout(workout_id):
    workout = WorkoutLog.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        abort(403)  # Forbidden access if the current user does not own the workout log   
    db.session.delete(workout)
    db.session.commit()   
    return redirect(url_for('dashboard'))

@app.route('/edit_workout_log/<int:workout_id>', methods=['GET', 'POST'])
@login_required
def edit_workout_log(workout_id):
    workout = WorkoutLog.query.get_or_404(workout_id)
    
    if workout.user_id != current_user.id:
        abort(403)  #access not allowed if user is not recognized

    form = WorkoutLogForm(obj=workout)
    if form.validate_on_submit():
        workout.exercise_name = form.exercise_name.data
        workout.intensity = form.intensity.data
        workout.duration = form.duration.data
        workout.log_date = form.log_date.data
        db.session.commit()       
        return redirect(url_for('dashboard'))
    return render_template('edit_workout_log.html', form=form, workout_id=workout_id)

@app.route('/workout_log_history')
@login_required
def workout_log_history():
    user_id = current_user.id
    workouts = WorkoutLog.query.filter_by(user_id=user_id).order_by(WorkoutLog.log_date.desc()).all()
    return render_template('workout_log_history.html', workouts=workouts)

@app.route('/select_workout_preference', methods=['GET', 'POST'])
@login_required
def select_workout_preference():
    form = WorkoutPreferenceForm()
    if form.validate_on_submit():
        session['preference'] = form.preference.data
        return redirect(url_for('select_workout_days'))
    return render_template('select_workout_preference.html', form=form)

@app.route('/select_workout_days', methods=['GET', 'POST'])
@login_required
def select_workout_days():
    form = WorkoutDaysForm()
    if form.validate_on_submit():
        session['days'] = form.days.data
        return redirect(url_for('display_workout_plan'))
    return render_template('select_workout_days.html', form=form)

@app.route('/display_workout_plan')
@login_required
def display_workout_plan():
    preference = session.get('preference')
    days = session.get('days')
    plan_template_name = f"{preference}_{days}_day_split.html"
    return render_template(plan_template_name)

def calculate_intensity(age, training_preference):
    base_intensity = max(10 - (age - 20) / 5, 1)  #base intensity is 10 and reduces slightly every 5 years the user is older 20 yrs
    if training_preference == 'cardio':
        return base_intensity * 1.1
    elif training_preference == 'weight':
        return base_intensity * 0.9
    return base_intensity

def calculate_volume(current_weight, goal_weight, training_preference, age):
    weight_change_needed = abs(current_weight - goal_weight)
    base_volume = weight_change_needed * 5  

    # volume is adjusted based on users preference
    if age < 30:
        # Increase the base volume for users under 30, first value was 1, then 1.1, then settled on 1.2
        base_volume *= 1.2

    # Volume adjusted for training preference
    if training_preference == 'hybrid':
        base_volume *= 1.1
    elif training_preference == 'cardio':
        base_volume *= 0.8

    # Adjustments for people over 30 yrs. General statement - the volume is reduced for people of different age groups to take higher recovery time into account
    if age >= 30:
        if age > 60:
            # Volume is decreased for older people
            age_factor = 0.5
        elif age > 50:
            # Moderate decrease for those over 50
            age_factor = 0.75
        else:
            # Standard age factor for users between 30 and 50
            age_factor = 1
        base_volume *= age_factor

    # Tried to keep the volume within a safe range, this is too ensure users have sufficient recovery time regardless of age
    safe_volume = max(min(base_volume, 70), 10)  # Volume is kept between 10 and 70 MAX!

    return safe_volume


def workout_sessions_per_week(age, training_preference):  #users below 40 yrs are more than capable of training 5 times a week, at their preffered intensity
    if age < 40:
        base_sessions = 5
    else:
        base_sessions = 3
    if training_preference == 'hybrid':
        return min(base_sessions + 1, 7)
    return base_sessions



def adjust_workout_volume(user, base_volume):
    if user.goal_weight > user.current_weight:
        return base_volume * 1.1
    else:
        return base_volume * 0.9

def calculate_nutritional_goals(user):
    # Constants for macronutrient caloric values in nutrional sceince
    CALORIES_PER_GRAM_PROTEIN = 4
    CALORIES_PER_GRAM_CARBS = 4
    CALORIES_PER_GRAM_FAT = 9

    # base calorie intake
    if user.goal_weight < user.current_weight:
        # calorie defecit
        daily_calories = user.tdee - 250 #chose the value 250 as its the safest number preventing any adverse effects in the human body
        caloric_goal_statement = f"To lose weight, aim for a daily caloric intake of about {daily_calories:.0f} calories."
    elif user.goal_weight > user.current_weight:
        # calorie surplus
        daily_calories = user.tdee + 250
        caloric_goal_statement = f"To gain weight, aim for a daily caloric intake of about {daily_calories:.0f} calories."
    else:
        # Maintenance
        daily_calories = user.tdee
        caloric_goal_statement = f"To maintain your current weight, aim for a daily caloric intake of about {daily_calories:.0f} calories."
        
    # Macronutrional goals for the user based on their inputs
    if user.training_preference == 'weight':
        protein_ratio = 0.30  # i made a higher protein ratio for higher protein intake
        fat_ratio = 0.25
        carb_ratio = 0.45
    elif user.training_preference == 'cardio':
        protein_ratio = 0.25
        fat_ratio = 0.20
        carb_ratio = 0.55  # Higher carbs for energy 
    else:  # this is for Hybrid or balanced training
        protein_ratio = 0.25
        fat_ratio = 0.30
        carb_ratio = 0.45

    # calculate macronutrient intake for the user (in grams)
    protein_grams = (daily_calories * protein_ratio) / CALORIES_PER_GRAM_PROTEIN
    fat_grams = (daily_calories * fat_ratio) / CALORIES_PER_GRAM_FAT
    carb_grams = (daily_calories * carb_ratio) / CALORIES_PER_GRAM_CARBS

    return {
        'daily_calories': daily_calories,
        'protein_grams': round(protein_grams, 1),
        'fat_grams': round(fat_grams, 1),
        'carb_grams': round(carb_grams, 1),
        'caloric_goal_statement': caloric_goal_statement  
    }

def generate_workout_plan(user):
    intensity = calculate_intensity(user.age, user.training_preference)
    base_volume = calculate_volume(user.current_weight, user.goal_weight, user.training_preference, user.age)
    adjusted_volume = adjust_workout_volume(user, base_volume)
    sessions_per_week = workout_sessions_per_week(user.age, user.training_preference)
    nutrition = calculate_nutritional_goals(user)

    # simple description for intensity, this is based on the intensity fucntion above
    if intensity < 4:
        intensity_description = 'Light intensity. consider increasing intensity over time.'
    elif intensity < 7:
        intensity_description = 'Moderate intensity. Aim to have a few reps left in the tank after your sets.'
    else:
        intensity_description = 'High intensity. Push yourself close to your limits (failure), ensuring proper form.'

    
    volume_description = f'Your weekly exercise volume is recommended to be {adjusted_volume:.1f} sets. Distribute this evenly over your sessions.'

    

    # Compile the assessment details - just returns all the results for the user in the form of statements
    return {
        'intensity_description': intensity_description,
        'volume_description': volume_description,
        'sessions_per_week': f'{sessions_per_week} sessions per week.',
        'focus': f'Focus on {user.training_preference.title()} intensive training.',
        'nutrition': nutrition,
        
    }
    

@app.route('/workout', methods=['GET', 'POST'])
@login_required
def workout():
    form = WorkoutPlanForm()
    if form.validate_on_submit():
        user = current_user  
        user.age = form.age.data
        user.current_weight = form.current_weight.data
        user.goal_weight = form.goal_weight.data
        user.training_preference = form.training_preference.data

        workout_plan = generate_workout_plan(user)
        return render_template('workout_plan.html', plan=workout_plan)
    return render_template('workout_form.html', form=form)


def calculate_bmi(height, weight):
    return weight / (height ** 2)

def calculate_tdee(gender, height, weight, age, activity_level):  #Mifflin St jeor equation, which is an updated version of harris benedict equation for BMR (Base metabolic rate)
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    if activity_level == 'sedentary':
        tdee = bmr * 1.2
    elif activity_level == 'lightly_active':
        tdee = bmr * 1.375
    elif activity_level == 'moderately_active':
        tdee = bmr * 1.55
    else:
        tdee = bmr * 1.725
    return tdee

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
