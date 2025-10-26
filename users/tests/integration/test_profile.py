from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase

user = get_user_model()

class ProfileFlowTestCase(TestCase):
    """Prueba de integración: perfil de usuario."""

    def setUp(self):
        # Se ejecuta antes de cada test
        self.client = APIClient()
        self.user = user.objects.create_user(
            username="testuser",
            email="usuario@correo.com",
            password="StrongPass123!"
        )

        # Obtener token JWT para autenticación
        token_url = reverse('users:token_obtain_pair')
        response = self.client.post(token_url, {
            "username": "testuser",
            "password": "StrongPass123!"
        }, format='json')

        self.assertEqual(response.status_code, 200, f"No se pudo autenticar: {response.data}")

        # Añadir encabezado Authorization para peticiones autenticadas
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # URL del endpoint de perfil
        self.profile_url = reverse('users:profile')

    def test_view_and_edit_profile(self):
        """Verifica ver y editar el perfil del usuario."""

        # 1️⃣ Ver perfil
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200, f"No se pudo obtener el perfil: {response.data}")
        self.assertEqual(response.data['username'], "testuser")

        # 2️⃣ Editar perfil
        update_payload = {
            "username": "updateduser",
            "first_name": "NuevoNombre",
            "last_name": "NuevoApellido",
            "secret_question": "nombre_mascota",
            "secret_answer": "Fido",
            "current_password": "StrongPass123!"
        }


        response = self.client.put(self.profile_url, update_payload, format='json')
        self.assertIn(response.status_code, [200, 204], f"El PUT del perfil debería responder 200/204, obtuvo {response.status_code}: {response.data}")

        #Volver a obtener el perfil para verificar cambios
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code,200)

        self.assertEqual(response.data['username'], "updateduser")
        self.assertEqual(response.data['first_name'], "NuevoNombre")
        self.assertEqual(response.data['last_name'], "NuevoApellido")
        self.assertEqual(response.data['secret_question'], "nombre_mascota")

        # Por seguridad, la respuesta secreta no debe ser devuelta
        self.assertNotIn('secret_answer', response.data, "La respuesta secreta no debe ser devuelta en el perfil.")