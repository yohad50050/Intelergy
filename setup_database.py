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

            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"Database '{DB_NAME}' created or already exists.")

            # Use the database
            cursor.execute(f"USE {DB_NAME}")

            # Update authentication method for root user
            cursor.execute(
                "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY %s",
                (DB_PASSWORD,),
            )
            cursor.execute("FLUSH PRIVILEGES")
            print("Root user authentication updated.")

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
