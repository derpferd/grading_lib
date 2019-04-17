from setuptools import setup, find_packages


setup(
    name='grading_lib',
    version='3.0.4',
    description='A bunch of random grading functions',
    url='https://github.com/derpferd/grading_lib.git',
    author='Jonathan Beaulieu',
    author_email='123.jonathan@gmail.com',
    license='MIT',
    packages=find_packages(),
    package_data={
        'grading_lib.interface.web': [
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
        'docker',
    ],
    zip_safe=True,
)
