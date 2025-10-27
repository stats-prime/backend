from rest_framework import viewsets, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count, Min, Max, F, StdDev, Prefetch
from statistics import median
from .models import FarmEvent, FarmReward, FarmSource, FarmDrop, Game
from .serializers import (
    FarmEventSerializer,
    FarmDropSerializer,
    FarmSourceSerializer,
    FarmRewardSerializer,
    GameSerializer,
)

# -------------------------------
# Fuentes de farmeo (jefes, dominios, etc.)
# -------------------------------
class FarmSourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista las fuentes (jefes, dominios, etc.) de un juego específico.
    Permite filtrar por tipo si se desea (?type=jefe / ?type=dominio)
    """
    serializer_class = FarmSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        game_id = self.kwargs.get("game_pk")
        source_type = self.request.query_params.get("type")
        queryset = FarmSource.objects.filter(game__id=game_id)
    
        if source_type:
            # Normalizamos el texto (sin espacios, mayúsculas, tildes)
            normalized = source_type.strip().upper().replace(" ", "_")
    
            if normalized == "DOMINIO":
                queryset = queryset.filter(source_type__startswith="DOMINIO")
            else:
                queryset = queryset.filter(source_type__iexact=normalized)
    
        return queryset

# -------------------------------
# Eventos de farmeo
# -------------------------------
class FarmEventViewSet(viewsets.ModelViewSet):
    serializer_class = FarmEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        game_id = self.kwargs.get("game_pk")
        return FarmEvent.objects.filter(game_id=game_id)

    def perform_create(self, serializer):
        game_id = self.kwargs.get("game_pk")
        if not game_id:
            raise serializers.ValidationError({"non_field_errors": ["El ID del juego es requerido en la URL."]})

        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            raise serializers.ValidationError({"game": ["El juego especificado no existe."]})

        serializer.save(user=self.request.user, game=game)

    
# -------------------------------
# Listar las recompensas posibles de un jefe específico dentro de un juego
# -------------------------------
class FarmSourceRewardsView(generics.ListAPIView):
    serializer_class = FarmRewardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        game_id = self.kwargs.get('game_id')
        source_id = self.kwargs.get('source_id')
        return FarmReward.objects.filter(source__id=source_id, source__game__id=game_id)

# -------------------------------
# Estadísticas generales de farmeo
# -------------------------------
# -----------------------------
# Estadísticas personales por juego
# -----------------------------
class UserStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        game_id = request.query_params.get("game_id")
        source_name = request.query_params.get("source")  # nombre del jefe/dominio
        item_name = request.query_params.get("item")       # nombre del ítem
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not game_id:
            return Response({"error": "Debe especificar un game_id."}, status=400)

        # --- Filtrar eventos base ---
        events = FarmEvent.objects.filter(user=user, game__id=game_id)

        if source_name:
            events = events.filter(source__name__iexact=source_name)  # búsqueda por nombre

        # --- Filtro por fecha (rango inclusivo) ---
        if start_date:
            events = events.filter(date__gte=start_date)
        if end_date:
            events = events.filter(date__lte=end_date)

        # --- Drops relacionados (solo de los eventos filtrados) ---
        drops = FarmDrop.objects.filter(event__in=events)

        if item_name:
            drops = drops.filter(reward__name__iexact=item_name)

        # --- Cálculos principales ---
        total_events = events.count()
        total_drops = drops.aggregate(total=Sum("quantity"))["total"] or 0
        avg_drops = drops.aggregate(avg=Avg("quantity"))["avg"] or 0

        # --- Agrupar por ítem ---
        drops_grouped = (
            drops.values("reward__name", "reward__rarity")
            .annotate(
                total_quantity=Sum("quantity"),
                avg_quantity=Avg("quantity"),
                min_quantity=Min("quantity"),
                max_quantity=Max("quantity"),
                drop_count=Count("id"),
            )
            .order_by("-total_quantity")
        )

        # --- Distribución por tipo (JEFE, DOMINIO, etc.) ---
        by_type = (
            events.values("source__name", "farm_type")
            .annotate(count=Count("id"))
            .order_by("source__name")
        )

        # --- Promedio de drops por día ---
        by_day = (
            events.values("date")
            .annotate(avg_drops=Avg("drops__quantity"))
            .order_by("date")
        )

        return Response({
            "user": user.username,
            "game_id": game_id,
            "filters": {
                "source": source_name,
                "item": item_name,
                "start_date": start_date,
                "end_date": end_date,
            },
            "summary": {
                "total_events": total_events,
                "total_drops": total_drops,
                "avg_drops": round(avg_drops, 2),
            },
            "drops": drops_grouped,
            "by_type": list(by_type),
            "by_day": list(by_day),
        })
    
# --------------------
# Probabilidad de drop
# --------------------
class DropRateStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, game_id):
        user = request.user
        source_id = request.query_params.get("sourceID")
        item_id = request.query_params.get("itemID")

        if not source_id:
            return Response({"error": "Se requiere el parámetro sourceID."}, status=400)

        # Eventos del usuario para esa fuente
        total_events = FarmEvent.objects.filter(
            user=user, game__id=game_id, source__id=source_id
        ).count()

        if total_events == 0:
            return Response({
                "message": "No hay eventos registrados para esta fuente.",
                "drop_rate": 0
            })

        # Eventos en los que cayó el ítem (si se especifica)
        drops_qs = FarmDrop.objects.filter(
            event__user=user,
            event__game__id=game_id,
            event__source__id=source_id
        )

        if item_id:
            drops_qs = drops_qs.filter(reward__id=item_id)

        # Número de eventos únicos donde cayó ese ítem
        events_with_item = drops_qs.values("event").distinct().count()

        # Drop rate base
        drop_rate = events_with_item / total_events if total_events else 0

        # --- Drop rate por rareza ---
        rarity_data = drops_qs.values("reward__rarity").annotate(
            event_count=Count("event", distinct=True)
        )

        drop_rate_by_rarity = [
            {
                "rarity": r["reward__rarity"],
                "drop_rate": round(r["event_count"] / total_events, 3)
            }
            for r in rarity_data
        ]

        return Response({
            "game_id": game_id,
            "source_id": source_id,
            "item_id": item_id,
            "total_events": total_events,
            "events_with_item": events_with_item,
            "drop_rate": round(drop_rate, 3),
            "drop_rate_by_rarity": drop_rate_by_rarity
        })
    
# ---------------------
# Historial de eventos
# ---------------------
class FarmHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FarmEventSerializer

    def get_queryset(self):
        user_param = self.request.query_params.get('user')
        game_id = self.request.query_params.get('gameID')
        source_id = self.request.query_params.get('sourceID')
        type_param = self.request.query_params.get('type')

        # Si se pasa ?user=, buscar ese usuario; si no, usar el autenticado
        if user_param:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(username=user_param)
            except User.DoesNotExist:
                return FarmEvent.objects.none()
        else:
            user = self.request.user

        # Base query
        queryset = FarmEvent.objects.filter(user=user).order_by('-date')

        # Filtros opcionales
        if game_id:
            queryset = queryset.filter(game__id=game_id)
        if source_id:
            queryset = queryset.filter(source__id=source_id)
        if type_param:
            queryset = queryset.filter(source__type__iexact=type_param)

        # Prefetch para traer los drops relacionados en una sola consulta
        return queryset.prefetch_related(
            Prefetch('farmdrop_set', queryset=FarmDrop.objects.select_related('reward'))
        )
    
# -----------------------
# Vista de Estadisticas Globales
# -----------------------
class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]

class FarmStatsView(APIView):
    """
    Estadísticas globales por juego, con filtros opcionales:
    - type: tipo de farmevent (boss, weekly_boss, domain, etc.)
    - sourceID: ID de la fuente
    - itemID: ID del ítem
    - startDate / endDate: rango de fechas
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, game_id):
        # Filtros
        type_filter = request.query_params.get("type")          # tipo de farmevent
        source_id = request.query_params.get("sourceID")        # ID de jefe/fuente
        item_id = request.query_params.get("itemID")            # ID de ítem
        start_date = request.query_params.get("startDate")      # YYYY-MM-DD
        end_date = request.query_params.get("endDate")          # YYYY-MM-DD

        # Base: todos los eventos del juego
        events = FarmEvent.objects.filter(game__id=game_id)

        # Filtrar por tipo
        if type_filter:
            events = events.filter(farm_type__iexact=type_filter)

        # Filtrar por fuente
        if source_id:
            events = events.filter(source__id=source_id)

        # Filtrar por fechas (rango inclusivo)
        if start_date and end_date:
            events = events.filter(date__range=[start_date, end_date])
        elif start_date:
            events = events.filter(date__gte=start_date)
        elif end_date:
            events = events.filter(date__lte=end_date)

        # Drops relacionados
        drops = FarmDrop.objects.filter(event__in=events)
        if item_id:
            drops = drops.filter(reward__id=item_id)

        # Estadísticas generales
        total_events = events.count()
        total_drops = drops.aggregate(total=Sum('quantity'))['total'] or 0
        avg_drops = drops.aggregate(avg=Avg('quantity'))['avg'] or 0

        # Agrupar por ítem y rareza
        drops_grouped = (
            drops.values("reward__name", "reward__rarity")
            .annotate(
                total_quantity=Sum("quantity"),
                avg_quantity=Avg("quantity"),
                min_quantity=Min("quantity"),
                max_quantity=Max("quantity"),
                drop_count=Count("id"),
                stddev_quantity=StdDev("quantity"),
            )
            .order_by("-total_quantity")
        )

        # Calcular mediana manualmente
        for g in drops_grouped:
            quantities = list(
                drops.filter(
                    reward__name=g["reward__name"],
                    reward__rarity=g["reward__rarity"]
                ).values_list("quantity", flat=True)
            )
            g["median_quantity"] = float(median(quantities)) if quantities else 0

        return Response({
            "game_id": game_id,
            "filters": {
                "type": type_filter,
                "sourceID": source_id,
                "itemID": item_id,
                "date_range": [start_date, end_date],
            },
            "summary": {
                "total_events": total_events,
                "total_drops": total_drops,
                "avg_drops": round(avg_drops, 2),
            },
            "drops": drops_grouped
        })