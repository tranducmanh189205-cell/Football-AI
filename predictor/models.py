from django.db import models

class League(models.Model):
    code = models.CharField(max_length=10, unique=True) # E0, SP1, I1, D1, F1
    name = models.CharField(max_length=100)              # Premier League, La Liga...
    country = models.CharField(max_length=50)           # Anh, Tây Ban Nha...
    logo_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.country})"

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    short_name = models.CharField(max_length=10, blank=True, null=True)
    league = models.ForeignKey(League, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    logo_url = models.CharField(max_length=255, default="https://cdn-icons-png.flaticon.com/512/53/53283.png")

    def __str__(self):
        return self.name

class Match(models.Model):
    STATUS_CHOICES = (
        ('UPCOMING', 'Sắp diễn ra'),
        ('FINISHED', 'Đã kết thúc'),
    )
    league = models.ForeignKey(League, on_delete=models.CASCADE, null=True, blank=True, related_name='matches')
    season = models.CharField(max_length=20, null=True, blank=True)
    matchday = models.IntegerField(null=True, blank=True)  # <-- THÊM DÒNG NÀY: Vòng đấu (1, 2, 3...)
    date = models.DateField(null=True, blank=True)
    kickoff_time = models.TimeField(null=True, blank=True)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    result = models.CharField(max_length=5, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='FINISHED')

    def __str__(self):
        return f"[{self.league.code if self.league else 'N/A'} - Vòng {self.matchday}] {self.home_team.name} vs {self.away_team.name}"

class PredictionHistory(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='predicted_home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='predicted_away_matches')
    predicted_home_goals = models.IntegerField()
    predicted_away_goals = models.IntegerField()
    predicted_result = models.CharField(max_length=5)
    mode = models.CharField(max_length=20, default='auto')
    
    actual_home_goals = models.IntegerField(null=True, blank=True)
    actual_away_goals = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"[{self.created_at.strftime('%d/%m')}] {self.home_team.name} vs {self.away_team.name}"