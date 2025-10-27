from django.db import models
from django.conf import settings

class Game(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class FarmSource(models.Model):
    SOURCE_TYPES = [
        ('JEFE', 'Jefe'),
        ('JEFE-SEMANAL', 'Jefe Semanal'),
        ('DOMINIO', 'Dominio'),
    ]
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=100)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='sources')

    class Meta:
        unique_together = ('name', 'game')

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class FarmEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    farm_type = models.CharField(max_length=20, choices=FarmSource.SOURCE_TYPES)
    source = models.ForeignKey(FarmSource, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='farm_events')

    def __str__(self):
        return f"{self.user.username} - {self.source.name} ({self.date})"
    
    @property
    def total_drops(self):
        return sum(drop.quantity for drop in self.drops.all())
    
class FarmDrop(models.Model):
    event = models.ForeignKey('FarmEvent', on_delete=models.CASCADE, related_name='drops')
    reward = models.ForeignKey('FarmReward', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.reward.name} x{self.quantity} ({self.event.user.username})"

    
class FarmReward(models.Model):
    RARITY_CHOICES = [
        ('COMUN', 'Común'),
        ('RARO', 'Raro'),
        ('EPICO', 'Épico'),
        ('LEGENDARIO', 'Legendario'),
    ]

    name = models.CharField(max_length=150)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES)
    source = models.ForeignKey(FarmSource, on_delete=models.CASCADE, related_name='rewards')
    
    class Meta:
        unique_together = ('name', 'rarity', 'source')  # 🔒 Evita duplicados por jefe

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()}) - {self.source.name}"

