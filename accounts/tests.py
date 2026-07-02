from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthFlowTests(TestCase):
    def test_signup_page_loads(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')

    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Kuchli-Parol-123',
            'password2': 'Kuchli-Parol-123',
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user('bor_user', 'test@example.com', 'parol12345')
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'yangi_user',
            'email': 'test@example.com',
            'password1': 'Kuchli-Parol-123',
            'password2': 'Kuchli-Parol-123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='yangi_user').exists())

    def test_login_and_dashboard_access(self):
        User.objects.create_user('testuser', 'test@example.com', 'Kuchli-Parol-123')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'Kuchli-Parol-123',
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))

        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/dashboard.html')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_logout(self):
        User.objects.create_user('testuser', 'test@example.com', 'Kuchli-Parol-123')
        self.client.login(username='testuser', password='Kuchli-Parol-123')
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('main:home'))

    def test_home_page_loads(self):
        response = self.client.get(reverse('main:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/home.html')
