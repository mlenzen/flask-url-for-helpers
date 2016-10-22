"""
flask_url_for_helpers
---------------------

Utilities to help generate URLs in Flask.
"""
from __future__ import absolute_import, unicode_literals
from contextlib import suppress
from collections import Iterable, defaultdict
from inspect import signature

from flask import url_for, request, Flask, Blueprint, current_app
from werkzeug.datastructures import MultiDict

__version__ = '0.0.1'


class URLForHelpers():
	"""This extension provides a few functions to generate URLs.

	`url_update`
	------------
	Used to generate a URL based on the current request selectively updating
	parameters and/or the endpoint.

	`url_for_class`
	-------------
	`url_for_class` can be called to get the a URL for a given object of a registered
	class. Classes are registered to endpoints using the
	`register_class` decorator. Parameters for the view are
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
	@ufh.register_class(Employee)
	def employee_view(id):
		employee = Employee.query.get_or_404(id)
		return render_template('employee.html', employee=employee)

	You can now call `ufh.url_for_class(some_employee)` instead of
	`url_for('.employee', id=some_employee.id)`

	By default, endpoint arguments will be taken from attributes
	of the passed object. You can also specify a mapping of how to
	generate the parameters from the object.

	@blueprint.route('/employee/<dept>/<employee_name>')
	@ufh.register_class(models.Employee, {
		'dept': lambda employee: employee.department.name,
		})
	def dept_employee_view(dept, name):
		employee = Employee.query\
			.filter_by(name=name)\
			.join('department')\
			.filter(Department.name == dept)\
			.one()
	"""

	def __init__(self, app=None):
		self.app = app
		self._app_class_registry = {}
		self._blueprint_class_registry = defaultdict(dict)
		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		app.context_processor(lambda: {
			'url_for_class': self.url_for_class,
			'url_update': self.url_update,
			})
		self._app_class_registry[app] = {}

	def url_update(self, endpoint=None, **kwargs):
		"""Return a URL based on current request updated using passed args.

		url_for is called using all current args (endpoint and kwargs) modified
		by the parameters passed. Pameters include both parameters that match
		the view signature and query string parameters.

		If the existing request is at `url_for('ep1', param1='p1', param2='p2')`
		* `url_update('ep2')` == `url_for('ep2', param1='p1', param2='p2')`
		* `url_update(param1='newp1')` == `url_for('ep1', param1='newp1', param2='p2')`
		* `url_update('ep2', param1='newp1')` == `url_for('ep2', param1='newp1', param2='p2')`

		Args:
			endpoint: If not None, new endpoint to generate URL for.
			**kwargs: Keyword args to pass to url_for to overwrite current args.
		"""
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

	def _app_registry(self, app):
		try:
			return self._app_class_registry[app]
		except KeyError:
			raise Exception('Flask-URL-For-Helpers not initialized for app')

	def _all_app_registries(self, app):
		"""Yield registries for app and all blueprints."""
		yield self._app_registry(app)
		for blueprint in app.blueprints.values():
			yield self._blueprint_class_registry[blueprint]

	def _get_app_class_endpoint(self, app, class_):
		for registry in self._all_app_registries(app):
			with suppress(KeyError):
				return registry[class_]
		raise ValueError('No view function registered for {}'.format(obj_type))

	def url_for_class(self, obj):
		"""Get a url for an object based on it's class.
		"""
		obj_type = type(obj)
		endpoint_name, extract_funcs = self._get_app_class_endpoint(current_app, obj_type)
		kwargs = {}
		for kwarg, extract_func in extract_funcs.items():
			kwargs[kwarg] = extract_func(obj)
		return url_for(endpoint_name, **kwargs)

	def register_class(self, class_, app_or_blueprint, extract_funcs=None):
		"""A decorator to register an endpoint as the way to display an object of
		`class_`.

		Args:
			class_: class to register to an endpoint
			get_funcs: optional mapping of endpoint argument names to functions
				that extract the appropriate value from an instance of the class.
		"""
		extract_funcs = extract_funcs and extract_funcs.copy() or {}

		def decorator(func):
			for arg in signature(func).parameters:
				if arg not in extract_funcs:
					extract_funcs[arg] = lambda obj: getattr(obj, arg)
			if isinstance(app_or_blueprint, Flask):
				endpoint_name = func.__name__
				registry = self._app_registry(app_or_blueprint)
			elif isinstance(app_or_blueprint, Blueprint):
				endpoint_name = '%s.%s' % (app_or_blueprint.name, func.__name__)
				registry = self._blueprint_class_registry[app_or_blueprint]
			registry[class_] = (endpoint_name, extract_funcs)
			return func
		return decorator
