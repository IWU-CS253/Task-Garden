import os
import app as flaskr
import unittest
import tempfile
from flask import session

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
        flaskr.app.testing = True
        self.app = flaskr.app.test_client()
        with flaskr.app.app_context():
            flaskr.init_db()
            db = flaskr.get_db()
            db.execute(
                "INSERT INTO user (email, password, water_count, plant_water_count) "
                "VALUES (?, ?, ?, ?)",
                ("julia@test.com", "password", 0, 0)
            )
            db.commit()

    def login_session(self):
        """Log in a fake user by setting session['user_id']."""
        with self.app.session_transaction() as sess:
            sess["user_id"] = 1  # first user inserted in setUp()

    def test_add_task(self):
        self.login_session()

        rv = self.app.post(
            "/add_task",
            data=dict(
                task_name='H',
                task_date='<strong>HTML</strong> allowed here',
                task_category='A category'
            ),
            follow_redirects=True
        )

        with flaskr.app.app_context():
            db = flaskr.get_db()
            row = db.execute("SELECT * FROM task WHERE user_id = 1").fetchone()

            self.assertIsNotNone(row)
            self.assertEqual(row["task_name"], "H")
            self.assertEqual(row["task_date"], "<strong>HTML</strong> allowed here")
            self.assertEqual(row["task_category"], "A category")
            self.assertEqual(row["task_status"], 0)

        self.assertIn(b"H", rv.data)
        self.assertIn(b"<strong>HTML</strong> allowed here", rv.data)
        self.assertIn(b"A category", rv.data)

    def test_water_plant(self):
        self.login_session()

        with flaskr.app.app_context():
            db = flaskr.get_db()

            db.execute(
                "UPDATE user SET water_count = ?, plant_water_count = ? WHERE user_id = ?",
                (5, 3, 1)
            )
            db.commit()

        rv = self.app.post("/water_plant", follow_redirects=True)

        with flaskr.app.app_context():
            db = flaskr.get_db()
            row = db.execute(
                "SELECT water_count, plant_water_count FROM user WHERE user_id = 1"
            ).fetchone()

            self.assertEqual(row["water_count"], 4)

            self.assertEqual(row["plant_water_count"], 4)

        self.assertIn(b"Focus", rv.data)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flaskr.app.config['DATABASE'])

if __name__ == '__main__':
    unittest.main()