import time
import requests
from django.core.management.base import BaseCommand
from predictor.models import League, Team

# 1. Dán mã API Token bạn vừa copy ở Bước 1 vào đây
API_TOKEN = "5abf5299f9174cf49a99084ebbb0a121"

# Danh sách mã giải đấu trên Football-Data.org tương ứng với mã trong DB của bạn
LEAGUE_CODES = {
    "PL": "E0",    # Premier League (Anh)
    "PD": "SP1",   # Primera Division / La Liga (Tây Ban Nha)
    "SA": "I1",    # Serie A (Ý)
    "BL1": "D1",   # Bundesliga (Đức)
    "FL1": "F1",   # Ligue 1 (Pháp)
}

class Command(BaseCommand):
    help = "Tải toàn bộ logo chính thức của 5 giải đấu hàng đầu châu Âu từ Football-Data.org về MySQL"

    def handle(self, *args, **options):
        if API_TOKEN == "DIEN_API_TOKEN_CUA_BAN_VAO_DAY":
            self.stdout.write(self.style.ERROR("Bạn chưa điền API_TOKEN vào file script!"))
            return

        headers = {"X-Auth-Token": API_TOKEN}
        total_updated = 0

        self.stdout.write(self.style.NOTICE("Đang kết nối Football-Data.org để lấy logo các đội..."))

        for api_code, db_code in LEAGUE_CODES.items():
            url = f"https://api.football-data.org/v4/competitions/{api_code}/teams"
            league = League.objects.filter(code=db_code).first()

            self.stdout.write(f"\n--- Đang xử lý giải đấu mã: {api_code} ({db_code}) ---")
            
            try:
                res = requests.get(url, headers=headers, timeout=20)
                
                # Tránh vượt quá giới hạn 10 requests/phút của gói miễn phí
                if res.status_code == 429:
                    self.stdout.write(self.style.WARNING("Gói Free chạm giới hạn tần suất. Nghỉ 60 giây..."))
                    time.sleep(60)
                    res = requests.get(url, headers=headers, timeout=20)

                if res.status_code != 200:
                    self.stdout.write(self.style.WARNING(f"Không thể lấy danh sách giải {api_code}. Mã lỗi: {res.status_code}"))
                    continue

                teams_data = res.json().get("teams", [])
                league_updated = 0

                for t in teams_data:
                    name = t.get("name", "").strip()
                    short_name = t.get("shortName", "").strip()
                    crest_url = t.get("crest")

                    if not crest_url:
                        continue

                    # Tìm đội bóng trong Database
                    team = None
                    if short_name:
                        team = Team.objects.filter(name__icontains=short_name).first()
                    if not team and name:
                        team = Team.objects.filter(name__icontains=name).first()

                    # Nếu chưa có thì tạo mới và gán giải đấu
                    if not team:
                        team_name = short_name if short_name else name
                        team, _ = Team.objects.get_or_create(
                            name=team_name,
                            defaults={"league": league}
                        )

                    # Cập nhật logo
                    team.logo_url = crest_url
                    if league and not team.league:
                        team.league = league
                    team.save()

                    league_updated += 1
                    total_updated += 1
                    self.stdout.write(f"  + Cập nhật logo: {team.name}")

                self.stdout.write(self.style.SUCCESS(f"-> Hoàn tất giải {api_code}: Đã cập nhật {league_updated} đội."))
                
                # Tạm nghỉ 6 giây giữa các giải đấu để không bị lỗi 429 Rate Limit
                time.sleep(6)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Lỗi khi xử lý giải {api_code}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nHOÀN THÀNH TẤT CẢ! Đã cập nhật logo cho tổng cộng {total_updated} câu lạc bộ từ Football-Data.org."))