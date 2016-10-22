"""This module provides a few functions to generate URLs.

`url_for_obj`
-------------
`url_for_obj` can be called to get the a URL for a given object of a registered
class. Classes are registered to endpoints using the
`register_url_for_obj` decorator. Parameters for the view are
taken from attributes of the object or mapped in the decorator.

Let's say you have models:

class Employee(db.Model):

	id = Column(Integer, primary_key=True)
	name = Column(String)
	dept_id = Column(Integer, ForeignKey('department.id'))

	department = relationship(Department)

class Department(db.Model):

	id = Column(Integer, primary_key=True)
	name = Column(String, unique=True)

And a view for an individual employee:

ufh = flask_url_for_helpers.URLForHelpers()

@blueprint.route('/employee/<int:id>')
@ufh.register_url_for_obj(Employee)
def employee_view(id):
	employee = Employee.query.get_or_404(id)
	return render_template('employee.html', employee=employee)

You can now call `ufh.url_for_obj(some_employee)` instead of
`url_for('.employee', id=some_employee.id)`

By default, endpoint arguments will be taken from attributes
of the passed object. You can also specify a mapping of how to
generate the parameters from the object.

@blueprint.route('/employee/<dept>/<employee_name>')
@ufh.register_url_for_obj(models.Employee, {
	'dept': lambda employee: employee.department.name,
	})
def dept_employee_view(dept, name):
	employee = Employee.query\
		.filter_by(name=name)\
		.join('department')\
		.filter(Department.name == dept)\
		.one()
"""
from __future__ import absolute_import, unicode_literals
from collections import Iterable
from inspect import signature

from flask import url_for, request
from werkzeug.datastructures import MultiDict

__version__ = '0.0.1'


class URLForHelpers():

	def __init__(self, app=None):
		self.app = app
		self.url_for_obj_mapping = {}
		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		app.context_processor(lambda: {
			'url_for_obj': self.url_for_obj,
			'url_update': self.url_update,
			})

	def url_update(self, endpoint=None, **kwargs):
		"""Return the URL for passed endpoint using args from current request and kwargs."""
		# request.args contains parameters from the query string
		# request.view_args contains parameters that matched the view signature
		if endpoint is None:
			endpoint = request.endpoint
		args = MultiDict(request.args)
		args.update(request.view_args)
		for arg, value in kwargs.items():
			if isinstance(value, Iterable) and not isinstance(value, str):
				args.setlist(arg, value)
			else:
				args[arg] = value
		# Now set any individual args to the object instead of a list of len 1
		args = args.to_dict(flat=False)
		for key in set(args.keys()):
			if len(args[key]) == 1:
				args[key] = args[key][0]
		return url_for(endpoint, **args)

	def url_for_obj(self, obj):
		obj_type = type(obj)
		try:
			endpoint_name, extract_funcs = self.url_for_obj_mapping[obj_type]
			# render_func, blueprint, get_funcs = self.url_for_obj_mapping[obj_type]
		except KeyError:
			raise ValueError('No view function registered for {}'.format(obj_type))
		kwargs = {}
		for kwarg, extract_func in extract_funcs.items():
			kwargs[kwarg] = extract_func(obj)
		return url_for(endpoint_name, **kwargs)


	def register_url_for_obj(self, class_, blueprint=None, extract_funcs=None):
		"""A decorator to register an endpoint as the way to display an object of
		`class_`.

		Args:
			class_: class to register to an endpoint
			get_funcs: optional mapping of endpoint argument names to functions
				that extract the appropriate value from an instance of the class.
		"""
		extract_funcs = extract_funcs and extract_funcs.copy() or {}

		def decorator(func):
			if blueprint:
				endpoint_name = '%s.%s' % (blueprint.name, func.__name__)
			else:
				endpoint_name = func.__name__
			for arg in signature(func).parameters:
				if arg not in extract_funcs:
					extract_funcs[arg] = lambda obj: getattr(obj, arg)
			self.url_for_obj_mapping[class_] = (endpoint_name, extract_funcs)
			return func
		return decorator
