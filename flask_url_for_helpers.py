from __future__ import absolute_import, unicode_literals
from collections import Iterable
from functools import wraps
from inspect import signature

from flask import url_for, request
from werkzeug.datastructures import MultiDict

# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
	from flask import _app_ctx_stack as stack
except ImportError:
	from flask import _request_ctx_stack as stack

__version__ = '0.0.1'


class URLForHelpers():

	def __init__(self, app=None):
		self.app = app
		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		app.jinja_env.update({
			'url_for_obj': url_for_obj,
			'url_update_args': url_update_args,
			'url_update_endpoint_args': url_update_endpoint_args,
			})


def url_update_args(**kwargs):
	"""Take the current URL and update paramters, keeping all unspecified the same."""
	return url_update_endpoint_args(request.endpoint, **kwargs)


def url_update_endpoint_args(endpoint, **kwargs):
	"""Return the URL for passed endpoint using args from current request and kwargs."""
	# request.args contains parameters from the query string
	# request.view_args contains parameters that matched the view signature
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


# TODO
#	store class_function_mapping in app context?
#	Don't assume it's part of a blueprint by adding '.' before the function name
# 	  Is there a way of checking? Should it be an option in register?

class url_for_obj():
	"""This class provides a function can be called to get
	the a URL for a given object. Classes are registered to endpoints to
	handle objects of that type using a decorator. Parameters for the view are
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

	@blueprint.route('/employee/<int:id>')
	@url_for_obj.register(Employee)
	def employee_view(id):
		employee = Employee.query.get_or_404(id)
		return render_template('employee.html', employee=employee)

	You can now call `url_for_obj(some_employee)` instead of
	`url_for('.employee', id=some_employee.id)`

	By default, endpoint arguments will be taken from attributes
	of the passed object. You can also specify a mapping of how to
	generate the parameters from the object.

	@blueprint.route('/employee/<dept>/<employee_name>')
	@url_for_obj.register(models.Employee, {
		'dept': lambda employee: employee.department.name,
		})
	def dept_employee_view(dept, name):
		employee = Employee.query\
			.filter_by(name=name)\
			.join('department')\
			.filter(Department.name == dept)\
			.one()
	"""

	class_function_mapping = {}

	@classmethod
	def __call__(cls, obj):
		obj_type = type(obj)
		try:
			render_func, get_funcs = cls.class_function_mapping[obj_type]
		except KeyError:
			raise ValueError('No view function registered for {}'.format(obj_type))
		kwargs = {}
		for arg in signature(render_func).parameters:
			if arg in get_funcs:
				kwargs[arg] = get_funcs[arg](obj)
			else:
				kwargs[arg] = getattr(obj, arg)
		return url_for('.' + render_func.__name__, **kwargs)

	@classmethod
	def register(cls, class_, get_funcs=None):
		"""A decorator to register an endpoint as the way to display an object of
		`class_`.

		Args:
			class_: class to register to an endpoint
			get_funcs: optional mapping of endpoint argument names to functions
				that extract the appropriate value from an instance of the class.
		"""
		get_funcs = get_funcs or {}
		# TODO use wraps to not fuck up the signature

		def decorator(func):
			cls.class_function_mapping[class_] = (func, get_funcs)
			return func
		return decorator
