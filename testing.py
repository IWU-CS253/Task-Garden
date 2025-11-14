import os
import app as flaskr
import unittest
import tempfile

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
        flaskr.app.testing = True
        self.app = flaskr.app.test_client()
        with flaskr.app.app_context():
            flaskr.init_db()

    def test_messages(self):
        rv = self.app.post('/add_task', data=dict(
            task_name='H',
            task_date='<strong>HTML</strong> allowed here',
            task_category='A category',
            task_status='false'
        ), follow_redirects=True)
        assert b'No entries here so far' not in rv.data
        assert b'1' in rv.data
        assert b'H' in rv.data
        assert b'<strong>HTML</strong> allowed here' in rv.data
        assert b'A category' in rv.data

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flaskr.app.config['DATABASE'])

if __name__ == '__main__':
    unittest.main()