import flask
import flask_sqlalchemy
import pytest

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
