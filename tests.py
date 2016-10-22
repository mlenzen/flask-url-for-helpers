import flask
import flask_sqlalchemy
import pytest

from flask_url_for_helpers import url_for_obj, register_url_for_obj, url_update

db = flask_sqlalchemy.SQLAlchemy()

@pytest.fixture(scope='session')
def app(request):
	_app = flask.Flask(__name__)
	_app.config.update({
		'SERVER_NAME': 'localhost',
		'TESTING': True,
		'DEBUG': True,
		})
	db.init_app(_app)
	ctx = _app.app_context()
	ctx.push()

	def fin():
		ctx.pop()
	request.addfinalizer(fin)
	return _app


@pytest.fixture(scope='session')
def client(app):
	return app.test_client()


class Employee(db.Model):

	id = db.Column(db.Integer, primary_key=True)


class Manager(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String)
	last_name = db.Column(db.String)


def test_url_for_obj(app, client):

	@register_url_for_obj(Employee)
	@app.route('/employee/<int:id>')
	def employee_view(id):
		pass

	@register_url_for_obj(Manager, {
		'full_name': lambda manager: manager.first_name + '_' + manager.last_name,
		})
	@app.route('/manager/<full_name>')
	def manager_view(full_name):
		pass

	employee = Employee(id=1)
	assert url_for_obj(employee) == flask.url_for('employee_view', id=1)
	manager = Manager(first_name='M', last_name='Lenzen')
	assert url_for_obj(manager) == flask.url_for('manager_view', full_name='M_Lenzen')
