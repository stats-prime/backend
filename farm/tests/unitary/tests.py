from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from farm.models import Game, FarmSource, FarmEvent

class FarmEventTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(self.user)

        self.game = Game.objects.create(name='Genshin Impact')
        self.source = FarmSource.objects.create(name='Dungeon A', game=self.game)

    def test_create_farm_event_valid_source(self):
        """Debe crear un evento de farmeo correctamente"""
        url = reverse('game-farm-events-list', kwargs={'game_pk': self.game.id})
        data = {
            'source': self.source.id,
            'quantity': 10,
            'notes': 'Primera corrida'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FarmEvent.objects.count(), 1)
        self.assertEqual(FarmEvent.objects.first().user, self.user)

    def test_create_farm_event_invalid_source(self):
        """Debe fallar si la fuente no pertenece al juego"""
        another_game = Game.objects.create(name='Honkai')
        invalid_source = FarmSource.objects.create(name='Dungeon B', game=another_game)

        url = reverse('game-farm-events-list', kwargs={'game_pk': self.game.id})
        data = {'source': invalid_source.id, 'quantity': 5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(FarmEvent.objects.count(), 0)
