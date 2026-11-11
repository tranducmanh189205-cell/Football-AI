import io
import time
import requests
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from predictor.models import League, Team, Match

# 5 giải đấu hàng đầu châu Âu
LEAGUES_CONFIG = [
    {"code": "E0", "name": "Premier League", "country": "Anh"},
    {"code": "SP1", "name": "La Liga", "country": "Tây Ban Nha"},
    {"code": "I1", "name": "Serie A", "country": "Ý"},
    {"code": "D1", "name": "Bundesliga", "country": "Đức"},
    {"code": "F1", "name": "Ligue 1", "country": "Pháp"},
]

# Tự động khởi tạo danh sách toàn bộ các mùa từ 1993 đến 2027
SEASONS = []

# Giai đoạn 1993-1994 đến 1998-1999 (9394 -> 9899)
for y in range(93, 99):
    SEASONS.append(f"{y}{y+1}")

# Mùa chuyển giao thế kỷ 1999-2000
SEASONS.append("9900")

# Giai đoạn 2000-2001 đến 2008-2009 (0001 -> 0809)
for y in range(0, 9):
    SEASONS.append(f"0{y}0{y+1}")

# Mùa 2009-2010
SEASONS.append("0910")

# Giai đoạn 2010-2011 đến 2026-2027 (1011 -> 2627)
for y in range(10, 27):
    SEASONS.append(f"{y}{y+1}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

class Command(BaseCommand):
    help = "Cào toàn bộ lịch sử các mùa giải từ 1993 đến nay cho 5 giải đấu lớn vào MySQL"

    def handle(self, *args, **options):
        # 1. Đảm bảo các giải đấu đã tồn tại trong DB
        league_objs = {}
        for l_cfg in LEAGUES_CONFIG:
            league, _ = League.objects.get_or_create(
                code=l_cfg["code"],
                defaults={"name": l_cfg["name"], "country": l_cfg["country"]}
            )
            league_objs[l_cfg["code"]] = league

        total_processed_all = 0

        # 2. Vòng lặp duyệt qua từng giải đấu và từng mùa
        for l_cfg in LEAGUES_CONFIG:
            l_code = l_cfg["code"]
            league = league_objs[l_code]
            self.stdout.write(self.style.NOTICE(f"\n======================================================="))
            self.stdout.write(self.style.NOTICE(f"=== BẮT ĐẦU CÀO TOÀN BỘ LỊCH SỬ: {league.name} ({l_code}) ==="))
            self.stdout.write(self.style.NOTICE(f"======================================================="))

            league_processed = 0

            for season in SEASONS:
                url = f"https://www.football-data.co.uk/mmz4281/{season}/{l_code}.csv"
                res = None

                # Thử kết nối tối đa 3 lần tránh timeout hoặc nghẽn mạng
                for retry in range(3):
                    try:
                        res = requests.get(url, headers=HEADERS, timeout=20)
                        if res.status_code == 200:
                            break
                    except Exception:
                        time.sleep(1.5)

                if not res or res.status_code != 200:
                    continue

                try:
                    # Đọc nội dung CSV
                    content = res.content.decode('utf-8', errors='ignore')
                    if not content.strip():
                        continue

                    df = pd.read_csv(io.StringIO(content))
                    
                    # Kiểm tra các cột bắt buộc tối thiểu
                    required_cols = {'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR'}
                    if not required_cols.issubset(df.columns):
                        continue

                    df = df.dropna(subset=['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR'])
                    season_count = 0

                    for _, row in df.iterrows():
                        home_name = str(row['HomeTeam']).strip()
                        away_name = str(row['AwayTeam']).strip()

                        if not home_name or not away_name or home_name.lower() == 'nan':
                            continue

                        # Khởi tạo hoặc tìm câu lạc bộ
                        h_team, _ = Team.objects.get_or_create(name=home_name, defaults={'league': league})
                        a_team, _ = Team.objects.get_or_create(name=away_name, defaults={'league': league})

                        if h_team.league is None:
                            h_team.league = league
                            h_team.save()
                        if a_team.league is None:
                            a_team.league = league
                            a_team.save()

                        # Xử lý parse ngày thi đấu (các mùa cũ thường dùng d/m/y 2 số)
                        date_str = str(row['Date']).strip()
                        match_date = None
                        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
                            try:
                                parsed = datetime.strptime(date_str, fmt)
                                # Khắc phục trường hợp năm 2 số 9x bị hiểu nhầm thành 209x
                                if parsed.year > 2030:
                                    parsed = parsed.replace(year=parsed.year - 100)
                                match_date = parsed.date()
                                break
                            except ValueError:
                                pass

                        try:
                            h_score = int(float(row['FTHG']))
                            a_score = int(float(row['FTAG']))
                        except (ValueError, TypeError):
                            continue

                        result_val = str(row['FTR']).strip().upper()
                        if result_val not in ['H', 'D', 'A']:
                            continue

                        # Dùng update_or_create để cập nhật hoặc tạo mới
                        Match.objects.update_or_create(
                            league=league,
                            date=match_date,
                            home_team=h_team,
                            away_team=a_team,
                            defaults={
                                'season': season,
                                'home_score': h_score,
                                'away_score': a_score,
                                'result': result_val,
                                'status': 'FINISHED'
                            }
                        )
                        season_count += 1
                        league_processed += 1
                        total_processed_all += 1

                    self.stdout.write(f"  + Mùa {season}: Đã xử lý {season_count} trận.")
                    time.sleep(0.4)  # Nghỉ nhẹ giữa mỗi mùa để không bị ngắt kết nối

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  - Lỗi xử lý mùa {season}: {e}"))

            self.stdout.write(self.style.SUCCESS(f"-> Hoàn tất giải {league.name}: Tổng {league_processed} trận đấu."))

        self.stdout.write(self.style.SUCCESS(f"\n======================================================="))
        self.stdout.write(self.style.SUCCESS(f"HOÀN THÀNH TẤT CẢ! Tổng cộng đã nạp {total_processed_all} trận từ 1993 đến nay vào MySQL."))
        self.stdout.write(self.style.SUCCESS(f"======================================================="))