import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_database():
    # Get credentials from environment variables
    DB_USERNAME = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "intelergy")

    try:
        # First try to connect to MySQL server
        connection = mysql.connector.connect(
            host=DB_HOST, user=DB_USERNAME, password=DB_PASSWORD
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"Database '{DB_NAME}' created or already exists.")

            # Use the database
            cursor.execute(f"USE {DB_NAME}")

            # Grant privileges
            grant_query = f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USERNAME}'@'localhost' IDENTIFIED BY '{DB_PASSWORD}'"
            cursor.execute(grant_query)
            cursor.execute("FLUSH PRIVILEGES")
            print(f"Privileges granted to user '{DB_USERNAME}'")

            return True

    except Error as e:
        print(f"Error: {e}")
        return False

    finally:
        if "connection" in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")


if __name__ == "__main__":
    if setup_database():
        print("Database setup completed successfully!")
        print("\nNow you can run:")
        print("1. python -m device_data_collector.models")
        print("2. python create_test_user.py")
    else:
        print(
            "Database setup failed. Please check your MySQL credentials and permissions."
        )
