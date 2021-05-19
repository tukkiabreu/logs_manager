from setuptools import setup, find_packages
import logs_manager

setup(
    name='logs_manager',
    version=logs_manager.__version__,

    packages=find_packages(),
    entry_points={
        'console_scripts': [
        ]
    }
)