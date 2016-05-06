from setuptools import setup, find_packages

version = '1.8.1'

long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')

setup(
    name='netsight.cloudstorage',
    version=version,
    description="Allows you to store large files in the cloud",
    long_description=long_description,
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='',
    author='Ben Cole',
    author_email='benc@netsight.co.uk',
    url='https://github.com/netsight/netsight.cloudstorage',
    license='gpl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['netsight', ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'plone.api',
        'redis',
        'celery',
        'boto',
        'requests>=2.5.0',
        'collective.monkeypatcher',
        'plone.browserlayer',
    ],
    extras_require={'test': [
        'plone.app.testing',
    ]},
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
    setup_requires=[],
)
