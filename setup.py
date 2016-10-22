"""
Flask-URL-For-Helpers
-------------

This is the description for that library
"""
import os.path
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
	"""TestCommand to run py.test."""

	def finalize_options(self):
		"""Finalize option before test is run."""
		TestCommand.finalize_options(self)
		self.test_args = ['tests.py']
		self.test_suite = True

	def run_tests(self):
		"""Run tests."""
		import pytest
		errcode = pytest.main(self.test_args)
		sys.exit(errcode)


# Get the long description from the relevant file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
	long_description = f.read()


setup(
	name='Flask-URL-For-Helpers',
	version='0.0.1',
	description='Helpers for generating URLs in Flask.',
	long_description=long_description,
	author='Michael Lenzen',
	author_email='m.lenzen@gmail.com',
	license='BSD',
	url='https://github.com/mlenzen/flask-url-for-helpers',
	py_modules=['flask_url_for_helpers'],
	include_package_data=True,
	zip_safe=False,
	package_data={
		'': ['README.rst', 'LICENSE'],
	},
	install_requires=[
		'setuptools',
		'Flask',
	],
	tests_require=[
		'pytest',
		'flask_sqlalchemy',
	],
	cmdclass=dict(
		test=PyTest,
	),
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'Topic :: Software Development',
		'License :: OSI Approved :: BSD License',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: Implementation :: PyPy',
		'Environment :: Web Environment',
		'Operating System :: OS Independent',
		'Topic :: Software Development :: Libraries :: Python Modules'
	],
)
