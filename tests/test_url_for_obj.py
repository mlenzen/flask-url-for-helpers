import flask
import flask_sqlalchemy
import pytest

from flask_url_for_helpers import url_for_obj, register_url_for_obj

db = flask_sqlalchemy.SQLAlchemy()


class Employee(db.Model):

	id = db.Column(db.Integer, primary_key=True)


class Manager(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String)
	last_name = db.Column(db.String)


def test_simple(app, client):

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
