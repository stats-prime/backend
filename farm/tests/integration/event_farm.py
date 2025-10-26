from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from farm.models import Game, FarmSource, FarmEvent

User = get_user_model()

class FarmEventViewSetIntegrationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="player1", password="secret123")
        self.client.login(username="player1", password="secret123")

        self.game = Game.objects.create(name="Genshin Impact")
        self.source = FarmSource.objects.create(
            name="Dominio de Artefactos",
            location="Liyue",
            source_type="DOMINIO",
            game=self.game
        )

        # ✅ Nuevo nombre del reverse + cambio de game_id → game_pk
        self.url = reverse("game-farm-events-list", kwargs={"game_pk": self.game.id})

    def test_create_event_successfully(self):
        payload = {"farm_type": "DOMINIO", "source": self.source.id}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FarmEvent.objects.count(), 1)
        event = FarmEvent.objects.first()
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.source, self.source)

    def test_list_user_events(self):
        FarmEvent.objects.create(
            user=self.user,
            farm_type="DOMINIO",
            source=self.source,
            game=self.game
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["farm_type"], "DOMINIO")

    def test_cannot_create_event_without_auth(self):
        self.client.logout()
        payload = {"farm_type": "DOMINIO", "source": self.source.id}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
