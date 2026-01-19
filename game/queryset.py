from django.db import models

class GameQuerySet(models.QuerySet):
    def _all_games_played(self, user):
        return self.filter(
            models.Q(player_white=user)|models.Q(player_black=user)
        )
    
    def total_game_played(self, user):
        return self._all_games_played(user=user).count()
    
    def total_game_won(self, user):
        return self._all_games_played(user=user).filter(winner=user).count()
    
    def total_game_draw(self, user):
        return self._all_games_played(user=user).filter(
            winner=None, status="finished"
        ).count()