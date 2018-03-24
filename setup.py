from setuptools import setup


setup(
    name='grading_lib',
    version='2.0.0',
    description='A bunch of random grading functions',
    url='https://github.com/derpferd/grading_lib.git',
    author='Jonathan Beaulieu',
    author_email='123.jonathan@gmail.com',
    license='MIT',
    packages=['grading_lib'],
    package_data={
        'grading_lib': [
            'static/*',
            'static/highlight/*',
            'static/highlight/styles/*',
            'templates/*'
        ]
    },
    install_requires=[
        'flask',
        'click',
        'GitPython',
    ],
    zip_safe=True,
)
