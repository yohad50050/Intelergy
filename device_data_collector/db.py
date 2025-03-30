import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_USERNAME = os.getenv("DB_USERNAME", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "intelergy")

# Create database URL with proper escaping and configuration
DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USERNAME}:{quote_plus(DB_PASSWORD)}@{DB_HOST}/{DB_NAME}"
    "?auth_plugin=mysql_native_password"
    "&charset=utf8mb4"
)

# Create the declarative base that all models will use
Base = declarative_base()


class DatabaseHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            # Create engine with connection pooling and other optimizations
            self.engine = create_engine(
                DATABASE_URL,
                pool_size=20,
                pool_recycle=3600,
                pool_pre_ping=True,
                connect_args={"auth_plugin": "mysql_native_password"},
                echo=False,  # Set to True for SQL query logging
            )

            # Create session factory
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            self._initialized = True
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise

    @contextmanager
    def get_session(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
            self.Session.remove()

    def create_tables(self):
        """Create all tables defined in the models"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {str(e)}")
            raise


# Create a single instance of the database handler
db = DatabaseHandler()

# Create a session that can be imported by other modules
session = db.Session()
