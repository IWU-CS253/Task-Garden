import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, g, redirect, url_for, render_template, flash, session

# adapted from Flaskr
app = Flask(__name__)

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

@app.route('/', methods=['GET'])
def index():
    db = get_db()
    category = request.args.get('category')
    user_id = 1

    if category:
        cur = db.execute('select * from task where task_category = ? and user_id = ? and task_status != false order by task_date desc',
                         [category, user_id])
    else:
        cur = db.execute('Select * from task where user_id = ? and task_status != false Order by task_date DESC',
                         [user_id])
    categories = db.execute('select distinct task_category from task where task_category is not null and task_status != false').fetchall()
    task = cur.fetchall()

    return render_template('index.html', task=task, categories=categories)

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# end adaption from Flaskr

# will need to add water count manipulation later--separate function? or just another execute?
@app.route('/add_task', methods=['POST'])
def add_task():
    db = get_db()
    db.execute('insert into task (user_id, task_name, task_date, task_category, task_status) values (?, ?, ?, ?, ?)',
               [request.form['user_id'], request.form['task_name'], request.form['task_date'], request.form['task_category'], request.form["task_status"]])
    db.commit()

    flash('Successfully added task!')
    return redirect(url_for('index'))

@app.route('/complete_task', methods=['POST'])
def complete_task():
    db = get_db()
    db.execute('update task set task_status = true where taskid = ?',
               [request.form['taskid']])
    db.commit()

    flash('Successfully completed task!')
    return redirect(url_for('index'))

@app.route('/delete_task', methods=['POST'])
def delete_task():
    db = get_db()
    db.execute('delete from task where taskid = ?',
               [request.form['taskid']])
    db.commit()

    flash('Successfully completed task!')
    return redirect(url_for('index'))

@app.route('/view_inventory', methods=['POST'])
def view_inventory():
    return render_template('inventory.html')

@app.route('/completed_plants', methods=['POST'])
def completed_plants():
    return render_template('completed.html')

@app.route('/water_plant', methods=["POST"])
def water_plant():

    db = get_db()
    #user_id = session.get("user_id")
    session["user_id"] = 1
    user_id=session["user_id"]
    user_data = db.execute('SELECT water_count, plant_water_count FROM user WHERE user_id=?',
                           (user_id,)).fetchone()

    if user_data["water_count"] <= 0:
        flash("insufficient water")
        return redirect(url_for("index"))
    else:
        new_water = user_data["water_count"] - 1
        new_plant_water = user_data["plant_water_count"] + 1

    db.execute('UPDATE user SET water_count = ?, plant_water_count = ? WHERE user_id = ?', (new_water, new_plant_water, user_id))
    db.commit()
    return redirect(url_for("index"))
