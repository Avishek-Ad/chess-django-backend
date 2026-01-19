from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
import uuid
from useraccount.models import User

from .queryset import GameQuerySet


class ChessGame(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('finished', 'Finished')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player_white = models.ForeignKey(User, related_name="games_as_white", on_delete=models.CASCADE, null=True, blank=True)
    player_black = models.ForeignKey(User, related_name="games_as_black", on_delete=models.CASCADE, null=True, blank=True)
    move_history = models.JSONField(default=list)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    winner = models.ForeignKey(User, related_name="games_won", on_delete=models.SET_NULL, null=True, blank=True)
    board_fen = models.CharField(max_length=100, default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GameQuerySet.as_manager()

    def __str__(self):
        return f"Game {self.id} ({self.status})"