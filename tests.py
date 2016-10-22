"""Tests for flask_url_for_helpers."""
import flask
import flask_sqlalchemy
import pytest

from flask_url_for_helpers import url_for_obj, register_url_for_obj, url_update

app = flask.Flask(__name__)
app.config.update({
	'SERVER_NAME': 'localhost',
	'TESTING': True,
	'DEBUG': True,
	})
db = flask_sqlalchemy.SQLAlchemy()
db.init_app(app)


class Employee(db.Model):

	id = db.Column(db.Integer, primary_key=True)


class Manager(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String)
	last_name = db.Column(db.String)


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


@pytest.fixture(scope='session')
def app_context(request):
	ctx = app.app_context()
	ctx.push()
	request.addfinalizer(lambda: ctx.pop())
	return app


@pytest.fixture(scope='session')
def client(app_context):
	return app.test_client()


def test_url_for_obj_simple(client):
	employee = Employee(id=1)
	assert url_for_obj(employee) == flask.url_for('employee_view', id=1)


def test_url_for_obj_mapped(client):
	manager = Manager(first_name='M', last_name='Lenzen')
	assert url_for_obj(manager) == flask.url_for('manager_view', full_name='M_Lenzen')
