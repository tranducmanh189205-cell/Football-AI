import time
import requests
from datetime import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from predictor.models import League, Team, Match

# ==============================================================
# API TOKEN TỪ FOOTBALL-DATA.ORG
# ==============================================================
API_TOKEN = "5abf5299f9174cf49a99084ebbb0a121"

# Ánh xạ mã API sang mã League trong MySQL của bạn
LEAGUE_MAPPING = {
    "PL": "E0",    # Premier League (Anh)
    "PD": "SP1",   # La Liga (Tây Ban Nha)
    "SA": "I1",    # Serie A (Ý)
    "BL1": "D1",   # Bundesliga (Đức)
    "FL1": "F1",   # Ligue 1 (Pháp)
}

class Command(BaseCommand):
    help = "Tải toàn bộ lịch thi đấu (Vòng 1 - Vòng 38) của 5 giải đấu từ Football-Data.org và cập nhật trạng thái"

    def handle(self, *args, **options):
        if API_TOKEN == "DIEN_API_TOKEN_CUA_BAN_VAO_DAY":
            self.stdout.write(self.style.ERROR("Vui lòng kiểm tra lại API_TOKEN trong file!"))
            return

        headers = {"X-Auth-Token": API_TOKEN}
        today = timezone.now().date()
        total_fixtures = 0

        self.stdout.write(self.style.NOTICE("=== BẮT ĐẦU ĐỒNG BỘ TOÀN BỘ LỊCH THI ĐẤU ==="))

        for api_code, db_code in LEAGUE_MAPPING.items():
            league = League.objects.filter(code=db_code).first()
            if not league:
                continue

            self.stdout.write(f"\n--- Đang xử lý giải: {league.name} ({api_code}) ---")
            
            # Kéo toàn bộ danh sách trận của mùa giải (không lọc cứng status để lấy đủ các vòng)
            url = f"https://api.football-data.org/v4/competitions/{api_code}/matches"

            try:
                res = requests.get(url, headers=headers, timeout=25)

                # Giới hạn 10 requests/phút của gói Free
                if res.status_code == 429:
                    self.stdout.write(self.style.WARNING("Chạm trần gói Free API. Đang chờ 60 giây..."))
                    time.sleep(60)
                    res = requests.get(url, headers=headers, timeout=25)

                if res.status_code != 200:
                    self.stdout.write(self.style.WARNING(f"Không thể lấy dữ liệu giải {api_code}. Mã lỗi: {res.status_code}"))
                    continue

                matches_data = res.json().get("matches", [])
                league_count = 0

                # Lặp qua TOÀN BỘ các trận đấu trả về (không cắt [:15] nữa)
                for m in matches_data:
                    matchday_num = m.get("matchday")
                    utc_date_str = m.get("utcDate")
                    status_api = m.get("status")
                    score_data = m.get("score", {}).get("fullTime", {})

                    home_data = m.get("homeTeam", {})
                    away_data = m.get("awayTeam", {})

                    home_name = home_data.get("shortName") or home_data.get("name")
                    away_name = away_data.get("shortName") or away_data.get("name")
                    home_crest = home_data.get("crest")
                    away_crest = away_data.get("crest")

                    if not home_name or not away_name or not utc_date_str or not matchday_num:
                        continue

                    # 1. Tìm hoặc tạo Team
                    h_team, _ = Team.objects.get_or_create(name=home_name, defaults={'league': league})
                    a_team, _ = Team.objects.get_or_create(name=away_name, defaults={'league': league})

                    # Cập nhật logo nếu có
                    if home_crest and (not h_team.logo_url or "flaticon" in h_team.logo_url):
                        h_team.logo_url = home_crest
                        h_team.save()
                    if away_crest and (not a_team.logo_url or "flaticon" in a_team.logo_url):
                        a_team.logo_url = away_crest
                        a_team.save()

                    # 2. Quy đổi múi giờ UTC sang Giờ Việt Nam (UTC+7)
                    try:
                        utc_dt = datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        utc_dt = datetime.fromisoformat(utc_date_str.replace("Z", "+00:00"))

                    vn_dt = utc_dt + timezone.timedelta(hours=7)
                    match_date = vn_dt.date()
                    match_time = vn_dt.time()

                    # 3. Phân loại trạng thái trận đấu
                    if status_api == 'FINISHED' or match_date < today:
                        db_status = 'FINISHED'
                    else:
                        db_status = 'UPCOMING'

                    home_score = score_data.get("home")
                    away_score = score_data.get("away")
                    result_char = None
                    if home_score is not None and away_score is not None:
                        if home_score > away_score: result_char = 'H'
                        elif home_score < away_score: result_char = 'A'
                        else: result_char = 'D'

                    # 4. Lưu hoặc cập nhật vào bảng Match
                    existing_match = Match.objects.filter(
                        league=league,
                        home_team=h_team,
                        away_team=a_team,
                        matchday=matchday_num
                    ).first()

                    if existing_match:
                        existing_match.date = match_date
                        existing_match.kickoff_time = match_time
                        existing_match.status = db_status
                        if home_score is not None: existing_match.home_score = home_score
                        if away_score is not None: existing_match.away_score = away_score
                        if result_char: existing_match.result = result_char
                        existing_match.save()
                    else:
                        Match.objects.create(
                            league=league,
                            home_team=h_team,
                            away_team=a_team,
                            matchday=matchday_num,
                            date=match_date,
                            kickoff_time=match_time,
                            status=db_status,
                            home_score=home_score,
                            away_score=away_score,
                            result=result_char
                        )

                    league_count += 1
                    total_fixtures += 1

                self.stdout.write(self.style.SUCCESS(f"-> Hoàn tất giải {league.name}: Đã đồng bộ {league_count} trận đấu."))
                time.sleep(6)  # Nghỉ 6 giây an toàn giữa các request

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Lỗi khi xử lý giải {api_code}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nĐỒNG BỘ THÀNH CÔNG! Tổng cộng {total_fixtures} trận đấu đã được lưu/cập nhật."))