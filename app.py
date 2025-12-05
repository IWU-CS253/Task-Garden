import os
from math import floor
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, g, redirect, url_for, render_template, flash, session
from flask_session import Session

# adapted from Flaskr
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'garden.db'),
    SECRET_KEY='development key',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page"""
    db = get_db()
    user_id = session.get("user_id", None)

    # COMMENT OUT THESE TWO LINES FOR TESTING! (uncomment before committing changes)
    if user_id == None:
        return render_template("login.html")

    # Gets the amount of times the user has watered a plant
    result = db.execute(
        "SELECT plant_water_count FROM user WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    # Determines how much a given plant has been watered
    # If no plant has ever been watered, it is set to 11
    if result and result["plant_water_count"] == 0:
        plant_water = 11
    elif result:
        plant_water = result["plant_water_count"] % 10
    else:
        plant_water = 11

    # Determines which plant picture to display
    plant = 1
    if plant_water == 0:
        plant = 3
    elif plant_water < 5 or plant_water == 11:
        plant = 1
    elif plant_water < 10:
        plant = 2

    # Determines how much more water a plant needs to be finished growing
    if plant_water == 11:
        water_to_garden = 10
    elif result["plant_water_count"] % 10 == 0:
        water_to_garden = "Completed!"
    else:
        water_to_garden = 10 - (result["plant_water_count"] % 10)


    category = request.values.get('category')

    # Gets all unique categories from uncompleted tasks
    if category:
        cur = db.execute('select * from task where task_category = ? and user_id = ? and task_status = 0 order by task_date desc',
                         [category, user_id])
    else:
        cur = db.execute('Select * from task where user_id = ? and task_status = 0 Order by task_date DESC',
                         [user_id])
    categories = db.execute('select distinct task_category from task where user_id = ? and task_category is not null and task_status = 0',
                            [user_id]).fetchall()
    task = cur.fetchall()

    # Gets the total water the user has
    user_water = db.execute(
        "SELECT water_count FROM user WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    water_count = user_water["water_count"]

    return render_template('index.html', task=task, plant=plant, categories=categories, user_id=user_id, user_water=water_count, water_to_garden=water_to_garden)


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# end adaption from Flaskr

# will need to add water count manipulation later--separate function? or just another execute?
@app.route('/add_task', methods=['POST'])
def add_task():
    """Adds a task to the database."""
    db = get_db()
    user_id = session.get("user_id")

    db.execute('insert into task (user_id, task_name, task_date, task_category, task_status) values (?, ?, ?, ?, ?)',
               [user_id, request.form['task_name'], request.form['task_date'], request.form['task_category'], request.form["task_status"]])
    db.commit()

    flash('Successfully added task!')
    return redirect(url_for('index'))


@app.route('/complete_task', methods=['POST'])
def complete_task():
    """Marks a given task as completed"""
    db = get_db()
    user_id = session.get("user_id", None)

    # Marks the task clicked on as completed
    db.execute('update task set task_status = true where taskid = ?',
               [request.form['taskid']])

    # Gives the user +1 water
    water = db.execute("SELECT water_count FROM user WHERE user_id = ?",(user_id,)).fetchone()
    new_water = water["water_count"] + 1
    db.execute('UPDATE user SET water_count = ? WHERE user_id = ?',(new_water,user_id))

    db.commit()

    flash('Successfully completed task!')
    return redirect(url_for('index'))


@app.route('/delete_task', methods=['POST'])
def delete_task():
    """Completely deletes a task without giving water to the user."""
    db = get_db()
    db.execute('delete from task where taskid = ?',
               [request.form['taskid']])
    db.commit()

    flash('Successfully completed task!')
    return redirect(url_for('index'))


@app.route('/completed_tasks', methods=['GET'])
def view_completed_tasks():
    """Allows the user to view their completed tasks."""
    db = get_db()
    user_id = session.get("user_id", None)

    task = db.execute('Select * from task where user_id = ? and task_status = 1 Order by task_date DESC',
                     [user_id]).fetchall()

    return render_template('inventory.html', task=task)


@app.route('/completed_plants', methods=['GET'])
def completed_plants():
    """Shows the user all the plants they have completed"""
    db = get_db()
    user_id = session.get("user_id", None)

    # Gets the amount of times the user has watered a plant
    result = db.execute(
        "SELECT plant_water_count FROM user WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    # Determines how many plants to display
    if result:
        plants_completed = int(result["plant_water_count"]/10)
    else:
        plants_completed = 0
    return render_template('completed.html', plants_completed=plants_completed)


@app.route('/water_plant', methods=["POST"])
def water_plant():
    """Lets user water the current plant"""
    db = get_db()
    user_id = session.get("user_id", None)

    # Gets water data from database
    user_data = db.execute('SELECT water_count, plant_water_count FROM user WHERE user_id=?',
                           (user_id,)).fetchone()

    if user_data["water_count"] is not None:
        water = user_data["water_count"]
    else:
        water = 0
    if user_data["plant_water_count"] is not None:
        plant_water = user_data["plant_water_count"]
    else:
        plant_water = 0

    # If the user doesn't have any water, send them back to the main page
    if water <= 0:
        flash("insufficient water")
        return redirect(url_for("index"))

    new_water = water - 1
    new_plant_water = plant_water + 1

    # Update the database with the new water values
    db.execute(
        'UPDATE user SET water_count = ?, plant_water_count = ? WHERE user_id = ?',
        (new_water, new_plant_water, user_id)
    )
    db.commit()

    return redirect(url_for("index"))


@app.route('/create_user', methods=["POST"])
def create_user():
    """Allows the user to sign up"""
    db = get_db()

    email = request.form["email"]
    password = request.form["password"]

    # Prompts user to fill out the form
    if not email or not password:
        flash("Please fill out all fields")
    else:
        email_check = db.execute("select email from user where email = ?",
                           [email]).fetchone()
        if email_check:
            flash("Account already exists with this email, please login")
            return render_template("login.html")
        else:
            # Put the username and password in the database
            db.execute("insert into user (email, password, water_count, plant_water_count) VALUES (?, ?, 0, 0)",
                   [email, password])
            db.commit()

            return redirect(url_for("login_user_page"))


@app.route('/login_user', methods=["POST"])
def login_user():
    """Allows the user to log into their account"""
    db = get_db()

    email = request.form.get("email")
    password = request.form.get("password")

    # Prompts user to fill out form
    if not email or not password:
        flash("Please fill out all fields")
        return render_template("login.html")

    # Searches for the email and password
    else:
        login = db.execute("select user_id, email, password from user where email = ?",
                           [email]).fetchone()

        # Prompts user to create account if email doesn't exist
        if login is None:
            flash("User does not exist, please create account")
            return render_template("new_user.html")

        # Prompts user to retry password if it is incorrect
        elif login["password"] != password:
            flash("Password is incorect")
            return render_template("login.html")

        else:
            session["user_id"] = login["user_id"]
            return redirect(url_for("index"))

@app.route('/create_user_page', methods=["GET"])
def create_user_page():
    return render_template('new_user.html')

@app.route('/login_user_page', methods=["GET"])
def login_user_page():
    return render_template('login.html')

@app.route('/logout', methods=["GET"])
def logout_user():
    session["user_id"] = None
    return render_template('login.html')

@app.route('/timer', methods=["GET"])
def timer():
    """Allows the user to view their tasks through the timer page."""
    db = get_db()
    user_id = session.get("user_id", None)

    task = db.execute('Select * from task where user_id = ? and task_status = 0 Order by task_date DESC',
                      [user_id]).fetchall()

    return render_template('timer.html', task=task)