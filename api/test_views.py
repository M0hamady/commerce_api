import unittest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import User  # Adjust as per your User model path

class UserRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-registration')  # Ensure this matches your URL configuration

    def test_user_registration_success(self):
        # Test registration with valid data
        data = {
            'username': 'testuser3',
            'password': 'M@123456789',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_registration_invalid_data(self):
        # Create a user with an existing username
        existing_user = User.objects.create(username='existinguser')

        # Attempt registration with invalid data (existing username)
        data = {
            'username': 'existinguser',
            'password': 'M@123456789',
            'email': 'urfitness96@gmail.com',
            'first_name': 'esraa',
            'last_name': ''
        }
        response = self.client.post(self.register_url, data, format='json')

        # Assert that the response status code is HTTP 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that the response contains the expected error message
        self.assertIn('Username is already taken.', response.json().get('username', ''))

# Other test classes and methods can be defined similarly
class CustomLoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('custom-login')  # Adjust this based on your URL configuration

        # Create a user for testing login
        self.user = User.objects.create_user(username='testuser', password='M@123456789')

    def test_login_success(self):
        # Test login with correct credentials
        data = {
            'username': 'esraa',
            'password': '5555'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())  # Check if token is present in response

    def test_login_invalid_credentials(self):
        # Test login with incorrect password
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()['message'], 'Invalid username or password')

    def test_login_missing_username(self):
        # Test login without username
        data = {
            'password': 'M@123456789'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()['message'], 'Invalid username or password')

    def test_login_missing_password(self):
        # Test login without password
        data = {
            'username': 'esraa',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()['message'], 'Invalid username or password')

if __name__ == '__main__':
    unittest.main()
