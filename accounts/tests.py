from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import User

class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(identifier='alice', password='password123')
        self.client = APIClient()

    def test_login_with_username(self):
        # sanity check: user exists and password is correct
        self.assertTrue(User.objects.filter(username='alice').exists())
        self.assertTrue(self.user.check_password('password123'))

        # call Django authenticate directly to debug
        from django.contrib.auth import authenticate
        direct = authenticate(identifier='alice', password='password123')
        self.assertIsNotNone(direct, f"authenticate returned {direct}")

        resp = self.client.post(reverse('login'), {'identifier': 'alice', 'password': 'password123'})
        self.assertEqual(resp.status_code, 200, f"login failed, status {resp.status_code}, data {resp.data}")
        self.assertIn('access', resp.json(), f"response body {resp.data}")

    def test_login_invalid(self):
        resp = self.client.post(reverse('login'), {'identifier': 'alice', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 401)
