from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User


class PasswordResetBySecretFlowTestCase(TestCase):
    """Prueba de integración completa del flujo de restablecimiento de contraseña por pregunta secreta."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="TestUser",
            email="prueba@correo.com",
            password="Password123!",
            secret_question="¿Nombre de tu primer mascota?"
        )
        self.user.set_secret_answer("Fido")  # Método seguro definido en el modelo
        self.user.save()

        self.url = reverse("users:password_reset_secret")

    def test_a_get_secret_question(self):
        """✅ Debe devolver la pregunta secreta al enviar un identificador válido."""
        response = self.client.post(self.url, {"identifier": "TestUser"}, format="json")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"El endpoint debería responder 200, obtuvo {response.status_code}: {response.data}"
        )
        self.assertIn("secret_question", response.data)
        self.assertEqual(response.data["secret_question"], "¿Nombre de tu primer mascota?")

    def test_b_reset_password_correct_answer(self):
        """✅ Debe permitir cambiar la contraseña si la respuesta secreta es correcta."""
        response = self.client.put(self.url, {
            "identifier": "TestUser",
            "answer": "Fido",
            "new_password": "NewStrongPass123!"
        }, format="json")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Debería responder 200, obtuvo {response.status_code}: {response.data}"
        )
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Contraseña actualizada.")

        # Verificar que la nueva contraseña funcione
        login_url = reverse("users:token_obtain_pair")
        login_response = self.client.post(login_url, {
            "username": "TestUser",
            "password": "NewStrongPass123!"
        }, format="json")

        self.assertEqual(login_response.status_code, 200)
        self.assertIn("access", login_response.data)

    def test_c_reset_password_wrong_answer(self):
        """❌ No debe permitir cambiar contraseña si la respuesta es incorrecta."""
        response = self.client.put(self.url, {
            "identifier": "TestUser",
            "answer": "Malo",
            "new_password": "NewStrongPass123!"
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Respuesta secreta incorrecta.")

    def test_d_user_not_found(self):
        """❌ Debe devolver error si el usuario no existe."""
        response = self.client.post(self.url, {"identifier": "NoExiste"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "No existe usuario con ese identificador.")

    def test_e_missing_fields(self):
        """❌ Debe devolver error si faltan campos obligatorios."""
        response = self.client.put(self.url, {
            "identifier": "TestUser",
            "answer": ""
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "identifier, answer y new_password requeridos.")
        