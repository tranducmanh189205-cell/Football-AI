from django.core.management.base import BaseCommand
from predictor.models import Team

EPL_ALL_TEAMS = [
    {"name": "Arsenal", "short_name": "ARS", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t3.png"},
    {"name": "Aston Villa", "short_name": "AVL", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t7.png"},
    {"name": "Bournemouth", "short_name": "BOU", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t91.png"},
    {"name": "Brentford", "short_name": "BRE", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t94.png"},
    {"name": "Brighton", "short_name": "BHA", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t36.png"},
    {"name": "Chelsea", "short_name": "CHE", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t8.png"},
    {"name": "Crystal Palace", "short_name": "CRY", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t31.png"},
    {"name": "Everton", "short_name": "EVE", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t11.png"},
    {"name": "Fulham", "short_name": "FUL", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t54.png"},
    {"name": "Ipswich Town", "short_name": "IPS", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t40.png"},
    {"name": "Leicester", "short_name": "LEI", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t13.png"},
    {"name": "Liverpool", "short_name": "LIV", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t14.png"},
    {"name": "Man City", "short_name": "MCI", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t43.png"},
    {"name": "Man United", "short_name": "MUN", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t1.png"},
    {"name": "Newcastle", "short_name": "NEW", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t4.png"},
    {"name": "Nott'm Forest", "short_name": "NFO", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t17.png"},
    {"name": "Southampton", "short_name": "SOU", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t20.png"},
    {"name": "Tottenham", "short_name": "TOT", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t6.png"},
    {"name": "West Ham", "short_name": "WHU", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t21.png"},
    {"name": "Wolves", "short_name": "WOL", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t39.png"},
    # Các CLB truyền thống từng đá Ngoại hạng Anh
    {"name": "Blackburn", "short_name": "BLB", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t5.png"},
    {"name": "Bolton", "short_name": "BOL", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t30.png"},
    {"name": "Burnley", "short_name": "BUR", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t90.png"},
    {"name": "Cardiff", "short_name": "CAR", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t77.png"},
    {"name": "Charlton", "short_name": "CHA", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t33.png"},
    {"name": "Coventry", "short_name": "COV", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t9.png"},
    {"name": "Derby", "short_name": "DER", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t28.png"},
    {"name": "Huddersfield", "short_name": "HUD", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t38.png"},
    {"name": "Hull", "short_name": "HUL", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t88.png"},
    {"name": "Leeds", "short_name": "LEE", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t2.png"},
    {"name": "Luton", "short_name": "LUT", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t102.png"},
    {"name": "Middlesbrough", "short_name": "MID", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t25.png"},
    {"name": "Norwich", "short_name": "NOR", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t45.png"},
    {"name": "Portsmouth", "short_name": "POR", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t56.png"},
    {"name": "QPR", "short_name": "QPR", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t52.png"},
    {"name": "Reading", "short_name": "REA", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t108.png"},
    {"name": "Sheffield United", "short_name": "SHU", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t49.png"},
    {"name": "Sheffield Weds", "short_name": "SHW", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t19.png"},
    {"name": "Stoke", "short_name": "STK", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t110.png"},
    {"name": "Sunderland", "short_name": "SUN", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t57.png"},
    {"name": "Swansea", "short_name": "SWA", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t80.png"},
    {"name": "Watford", "short_name": "WAT", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t57.png"},
    {"name": "West Brom", "short_name": "WBA", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t35.png"},
    {"name": "Wigan", "short_name": "WIG", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t111.png"},
    {"name": "Wimbledon", "short_name": "WIM", "logo_url": "https://resources.premierleague.com/premierleague/badges/70/t23.png"}
]

class Command(BaseCommand):
    help = "Thêm danh sách toàn bộ câu lạc bộ Ngoại hạng Anh chuẩn tên dữ liệu Football-Data"

    def handle(self, *args, **options):
        count = 0
        for item in EPL_ALL_TEAMS:
            team, created = Team.objects.update_or_create(
                name=item["name"],
                defaults={
                    "short_name": item["short_name"],
                    "logo_url": item["logo_url"],
                }
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Thành công! Đã nạp và cập nhật {count} đội bóng Ngoại hạng Anh vào cơ sở dữ liệu."))