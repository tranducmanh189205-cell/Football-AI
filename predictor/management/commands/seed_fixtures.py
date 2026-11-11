from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from predictor.models import Team, Match

# Lịch các cặp đấu kèm khung giờ bóng lăn thực tế chuẩn Ngoại hạng Anh
UPCOMING_SCHEDULE = [
    {"home": "Arsenal", "away": "Chelsea", "days_ahead": 1, "kickoff": time(18, 30)},
    {"home": "Man United", "away": "Liverpool", "days_ahead": 1, "kickoff": time(21, 0)},
    {"home": "Man City", "away": "Tottenham", "days_ahead": 1, "kickoff": time(23, 30)},
    {"home": "Newcastle", "away": "Aston Villa", "days_ahead": 2, "kickoff": time(20, 0)},
    {"home": "Brighton", "away": "Wolves", "days_ahead": 2, "kickoff": time(22, 30)},
    {"home": "Everton", "away": "West Ham", "days_ahead": 3, "kickoff": time(2, 0)},
]

class Command(BaseCommand):
    help = "Cập nhật lịch thi đấu thời gian thực kèm giờ bóng lăn cụ thể"

    def handle(self, *args, **options):
        today = date.today()
        # Xóa các trận upcoming cũ để nạp mới chuẩn xác
        Match.objects.filter(status='UPCOMING').delete()

        count = 0
        for item in UPCOMING_SCHEDULE:
            h_team = Team.objects.filter(name__icontains=item["home"]).first()
            a_team = Team.objects.filter(name__icontains=item["away"]).first()

            if h_team and a_team:
                m_date = today + timedelta(days=item["days_ahead"])
                Match.objects.create(
                    home_team=h_team,
                    away_team=a_team,
                    date=m_date,
                    kickoff_time=item["kickoff"],
                    status='UPCOMING',
                    season='2026-27'
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Đã cập nhật thành công {count} trận đấu kèm GIỜ BÓNG LĂN chuẩn vào MySQL!"))