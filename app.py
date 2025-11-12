import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, g, redirect, url_for, render_template, flash

# adapted from Flaskr
# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# end adaption from Flaskr

# will need to add water count manipulation later--separate function?
@app.route('/add_task', methods=['POST'])
def add_task():
    db = get_db()
    db.execute('insert into task (task_name, task_date, task_category, task_status) values (?, ?, ?, ?)',
               [request.form['task_name'], request.form['task_date'], request.form['task_category'], request.form["task_status"]])
    db.commit()

    flash('Sucessfully added task!')
    return redirect(url_for['index'])

@app.route('/complete_task', methods=['POST'])
def complete_task():
    db = get_db()
    db.execute('update task set task_status = true where taskid = ?',
               [request.form['taskid']])
    db.commit()

    flash('Sucessfully completed task!')
    return redirect(url_for['index'])

@app.route('/delete_task', methods=['POST'])
def delete_task():
    db = get_db()
    db.execute('delete from task where taskid = ?'
               [request.form['taskid']])
    db.commit()

    flash('Sucessfully completed task!')
    return redirect(url_for['index'])