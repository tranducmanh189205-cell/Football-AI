import csv
import io
import urllib.request
from datetime import datetime
from django.core.management.base import BaseCommand
from predictor.models import Team, Match

class Command(BaseCommand):
    help = "Tải toàn bộ lịch sử các trận đấu Ngoại hạng Anh từ 1993 đến nay"

    def handle(self, *args, **options):
        self.stdout.write("Bắt đầu tải dữ liệu lịch sử Ngoại hạng Anh...")
        
        # Danh sách mã mùa giải từ 9394 đến 2425 (và các mùa gần nhất)
        seasons = []
        for y in range(93, 100):
            seasons.append(f"{y:02d}{(y+1)%100:02d}")
        for y in range(0, 26):
            seasons.append(f"{y:02d}{(y+1)%100:02d}")

        total_matches = 0

        for s in seasons:
            url = f"https://www.football-data.co.uk/mmz4281/{s}/E0.csv"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    reader = csv.DictReader(io.StringIO(content))

                    season_matches = 0
                    for row in reader:
                        home_name = row.get('HomeTeam')
                        away_name = row.get('AwayTeam')
                        fthg = row.get('FTHG')
                        ftag = row.get('FTAG')
                        ftr = row.get('FTR')
                        date_str = row.get('Date')

                        if not home_name or not away_name or fthg is None or ftag is None:
                            continue

                        # Chuẩn hóa ngày tháng
                        match_date = None
                        for fmt in ('%d/%m/%y', '%d/%m/%Y', '%Y-%m-%d'):
                            try:
                                match_date = datetime.strptime(date_str, fmt).date()
                                break
                            except (ValueError, TypeError):
                                pass

                        home_team, _ = Team.objects.get_or_create(name=home_name.strip())
                        away_team, _ = Team.objects.get_or_create(name=away_name.strip())

                        Match.objects.get_or_create(
                            season=s,
                            date=match_date,
                            home_team=home_team,
                            away_team=away_team,
                            defaults={
                                'home_score': int(fthg),
                                'away_score': int(ftag),
                                'result': ftr
                            }
                        )
                        season_matches += 1

                    total_matches += season_matches
                    self.stdout.write(self.style.SUCCESS(f"-> Mùa {s}: Đã nạp {season_matches} trận"))
            except Exception as e:
                # Bỏ qua nếu link mùa giải chưa có hoặc lỗi mạng nhẹ
                continue

        self.stdout.write(self.style.SUCCESS(f"HOÀN TẤT! Đã nạp thành công {total_matches} trận đấu vào MySQL."))