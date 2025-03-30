import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from device_data_collector.db import db
from device_data_collector.models import Base

# Load environment variables
load_dotenv()


def setup_database():
    # Get credentials from environment variables
    DB_USERNAME = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "intelergy")

    try:
        # First try to connect to MySQL server with additional parameters
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            auth_plugin="mysql_native_password",
            charset="utf8mb4",
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Drop the database if it exists
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
            print(f"Database '{DB_NAME}' dropped if it existed.")

            # Create database with proper character set
            cursor.execute(
                f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"Database '{DB_NAME}' created successfully.")

            # Select the database
            cursor.execute(f"USE {DB_NAME}")
            print(f"Using database '{DB_NAME}'")

            # Close MySQL connection before SQLAlchemy operations
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

            # Create tables using SQLAlchemy
            print("\nCreating database tables...")

            # Create all tables
            Base.metadata.create_all(db.engine)
            print("Database tables created successfully!")

            return True

    except Error as e:
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


if __name__ == "__main__":
    if setup_database():
        print("\nSetup completed successfully!")
        print("\nYou can now run:")
        print("python main_web_app.py")
    else:
        print("Setup failed. Please check your MySQL credentials and permissions.")
