from device_data_collector.models import session, User

# Create a test user
test_user = User(
    user_name="Test User", email="test@example.com", password="password123"
)

# Add to database
session.add(test_user)
session.commit()

print("Test user created successfully!")
print("Email: test@example.com")
print("Password: password123")
