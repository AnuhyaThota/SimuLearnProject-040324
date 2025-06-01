import os

class Config(object):
    """
    Configuration class for SimuLearnProject.
    """

    # Database URI for SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(f"{os.path.dirname(__file__)}/database/"), 'simulearn.db')

    # Uncomment the line below and provide the appropriate PostgreSQL credentials to use PostgreSQL instead of SQLite
    # SQLALCHEMY_DATABASE_URI = 'postgresql://tuser:tuserspassword@localhost/mydb'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for session management
    SECRET_KEY = 'you-will-never-guess'

    # Mail server configuration
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 8025
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_DEFAULT_SENDER = 'noreply@simulearn.com'

    

    


    