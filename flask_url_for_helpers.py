from __future__ import absolute_import, unicode_literals

from flask import current_app, abort

# Find the stack on which we want to store the database connection.
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
		pass
		if hasattr(app, 'teardown_appcontext'):
			app.teardown_appcontext(self.teardown)
		else:
			app.teardown_request(self.teardown)

	def teardown(self, exception):
		pass
