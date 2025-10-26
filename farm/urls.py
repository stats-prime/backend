from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    GameViewSet,
    FarmEventViewSet,
    FarmSourceViewSet,
    FarmSourceRewardsView,
    FarmStatsView,
    DropRateStatsView,
    FarmHistoryView,
    UserStatsView,
)

# Router principal
router = routers.SimpleRouter()
router.register(r'games', GameViewSet, basename='games')

# Router anidado: /games/<id>/farm-events, /games/<id>/farm-sources, etc.
games_router = routers.NestedSimpleRouter(router, r'games', lookup='game')
games_router.register(r'farm-events', FarmEventViewSet, basename='farm-event')
games_router.register(r'farm-sources', FarmSourceViewSet, basename='farm-source')

urlpatterns = [
    path('', include(router.urls)),          # /api/games/
    path('', include(games_router.urls)),    # /api/games/<id>/...
    
    # 🔹 Estadísticas personales
    path('user-stats/', UserStatsView.as_view(), name='user-stats'),
    
    # 🔹 Endpoints con ID de juego
    path('games/<int:game_id>/farm-sources/<int:source_id>/rewards/', 
         FarmSourceRewardsView.as_view(), name='farm-source-rewards'),

    path('games/<int:game_id>/farm-stats/', 
         FarmStatsView.as_view(), name='farm-stats'),

    path('games/<int:game_id>/stats/drop-rate/', 
         DropRateStatsView.as_view(), name='drop-rate-stats'),
         
    path('games/<int:game_id>/farm-events/history/', 
         FarmHistoryView.as_view(), name='farm-history'),
]