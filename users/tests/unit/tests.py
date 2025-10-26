from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTests(APITestCase):

    def setUp(self):
        # Endpoints principales
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:token_obtain_pair')
        self.profile_url = reverse('users:profile')
        self.secret_reset_url = reverse('users:password_reset_secret')

        # Datos base de usuario
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "first_name": "John",
            "last_name": "Doe",
            "secret_question": "¿Color favorito?",
            "secret_answer": "Azul"
        }

    def test_1_register_user(self):
        """✅ Debe registrar un nuevo usuario correctamente"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_2_login_user(self):
        """✅ Debe devolver token JWT al iniciar sesión"""
        User.objects.create_user(username="testuser", email="test@example.com", password="StrongPass123!")
        response = self.client.post(self.login_url, {"username": "testuser", "password": "StrongPass123!"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_3_profile_authenticated(self):
        """✅ Debe devolver el perfil del usuario autenticado"""
        user = User.objects.create_user(username="testuser", email="test@example.com", password="StrongPass123!")
        login = self.client.post(self.login_url, {"username": "testuser", "password": "StrongPass123!"}, format='json')
        token = login.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_4_password_reset_by_secret(self):
        """✅ Debe devolver la pregunta secreta del usuario"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            secret_question="¿Color favorito?"
        )
        user.set_secret_answer("Azul")
        user.save()

        response = self.client.post(self.secret_reset_url, {"identifier": "testuser"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("secret_question", response.data)

    def test_5_delete_account(self):
        """✅ Debe permitir eliminar la cuenta del usuario autenticado"""
        user = User.objects.create_user(username="testuser", email="test@example.com", password="StrongPass123!")
        login = self.client.post(self.login_url, {"username": "testuser", "password": "StrongPass123!"}, format='json')
        token = login.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.delete(self.profile_url, {"password": "StrongPass123!"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(username="testuser").exists())