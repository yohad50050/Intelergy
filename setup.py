from setuptools import setup, find_packages

setup(
    name="device_data_collector",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy",
        "mysql-connector-python",
        "python-dotenv",
        "requests",
        "flask",
        "flask-login",
    ],
)
