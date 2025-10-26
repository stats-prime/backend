from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class AuthFlowTestCase(TestCase):
    """Prueba de integración: registro y login de usuario."""

    def setUp(self):
        # Se ejecuta antes de cada test
        self.client = APIClient()

    def test_register_and_login(self):
        """Verifica el flujo completo de registro y login."""

        # 1️⃣ Registro
        register_url = reverse('users:register')
        payload = {
            "username": "nuevo_usuario",
            "email": "nuevo@correo.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }

        response = self.client.post(register_url, payload, format='json')

        self.assertEqual(
            response.status_code, 201,
            f"El registro debería responder 201, obtuvo {response.status_code}: {response.data}"
        )
        self.assertIn("email", response.data, "La respuesta debe incluir el email del usuario registrado.")

        # 2️⃣ Login
        login_url = reverse('users:token_obtain_pair')
        login_payload = {
            "username": "nuevo_usuario",
            "password": "StrongPass123!"
        }

        response = self.client.post(login_url, login_payload, format='json')

        self.assertEqual(
            response.status_code, 200,
            f"El login debería responder 200, obtuvo {response.status_code}: {response.data}"
        )
        self.assertIn("access", response.data, "La respuesta debe incluir el token de acceso.")
        self.assertIn("refresh", response.data, "La respuesta debe incluir el token de refresco.")
