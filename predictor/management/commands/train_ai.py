import os
import joblib
import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from predictor.models import Match, Team

class Command(BaseCommand):
    help = "Huấn luyện mô hình Machine Learning dự đoán bóng đá từ MySQL"

    def handle(self, *args, **options):
        self.stdout.write("1. Đang trích xuất dữ liệu trận đấu từ cơ sở dữ liệu...")
        
        matches = Match.objects.exclude(date__isnull=True).order_by('date')
        if matches.count() < 100:
            self.stdout.write(self.style.ERROR("Cơ sở dữ liệu chưa đủ trận đấu để train! Hãy chạy python manage.py crawl_epl trước."))
            return

        # Chuẩn bị dữ liệu dạng DataFrame
        records = []
        for m in matches:
            records.append({
                'date': m.date,
                'home_team': m.home_team.id,
                'away_team': m.away_team.id,
                'home_score': m.home_score,
                'away_score': m.away_score,
                'result': m.result  # 'H', 'D', 'A'
            })
        df = pd.DataFrame(records)

        self.stdout.write("2. Đang tạo các đặc trưng (Feature Engineering)...")

        # Feature: Tính phong độ trung bình trước mỗi trận đấu (Rolling 5 trận)
        # 3 điểm cho Win, 1 điểm cho Draw, 0 điểm cho Loss
        def get_team_points(row, team_id):
            if row['home_team'] == team_id:
                return 3 if row['result'] == 'H' else (1 if row['result'] == 'D' else 0)
            elif row['away_team'] == team_id:
                return 3 if row['result'] == 'A' else (1 if row['result'] == 'D' else 0)
            return 0

        # Feature ma trận huấn luyện
        X = []
        y = []

        team_matches_cache = {}
        for t_id in df['home_team'].unique():
            team_matches_cache[t_id] = df[(df['home_team'] == t_id) | (df['away_team'] == t_id)]

        for idx, row in df.iterrows():
            current_date = row['date']
            h_id = row['home_team']
            a_id = row['away_team']

            # Lấy 5 trận trước ngày thi đấu
            h_past = team_matches_cache[h_id][team_matches_cache[h_id]['date'] < current_date].tail(5)
            a_past = team_matches_cache[a_id][team_matches_cache[a_id]['date'] < current_date].tail(5)

            if len(h_past) < 3 or len(a_past) < 3:
                continue

            h_points = sum(get_team_points(r, h_id) for _, r in h_past.iterrows()) / len(h_past)
            a_points = sum(get_team_points(r, a_id) for _, r in a_past.iterrows()) / len(a_past)

            h_goals = sum(r['home_score'] if r['home_team'] == h_id else r['away_score'] for _, r in h_past.iterrows()) / len(h_past)
            a_goals = sum(r['away_score'] if r['away_team'] == a_id else r['home_score'] for _, r in a_past.iterrows()) / len(a_past)

            h_conceded = sum(r['away_score'] if r['home_team'] == h_id else r['home_score'] for _, r in h_past.iterrows()) / len(h_past)
            a_conceded = sum(r['home_score'] if r['away_team'] == a_id else r['away_score'] for _, r in a_past.iterrows()) / len(a_past)

            # Lịch sử đối đầu trước đó
            h2h_past = df[((df['home_team'] == h_id) & (df['away_team'] == a_id) | 
                          (df['home_team'] == a_id) & (df['away_team'] == h_id)) & (df['date'] < current_date)].tail(5)
            
            h2h_home_wins = sum(1 for _, r in h2h_past.iterrows() if (r['home_team'] == h_id and r['result'] == 'H') or (r['away_team'] == h_id and r['result'] == 'A'))
            h2h_total = len(h2h_past)
            h2h_rate = (h2h_home_wins / h2h_total) if h2h_total > 0 else 0.33

            features = [
                h_points,          # Phong độ đội nhà (0-3)
                a_points,          # Phong độ đội khách (0-3)
                h_goals,           # Hiệu suất ghi bàn đội nhà
                a_goals,           # Hiệu suất ghi bàn đội khách
                h_conceded,        # Bàn thua TB đội nhà
                a_conceded,        # Bàn thua TB đội khách
                h2h_rate           # Tỷ lệ thắng đối đầu của chủ nhà
            ]

            X.append(features)
            y.append(row['result'])

        X = np.array(X)
        y = np.array(y)

        self.stdout.write(f"-> Tạo xong {len(X)} mẫu huấn luyện.")

        # 3. Phân chia Train/Test và Huấn luyện
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

        self.stdout.write("3. Đang huấn luyện Random Forest Classifier...")
        clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
        clf.fit(X_train, y_train)

        acc = accuracy_score(y_test, clf.predict(X_test))
        self.stdout.write(self.style.SUCCESS(f"-> Độ chính xác kiểm thử (Test Accuracy): {acc*100:.2f}%"))

        # 4. Xuất file mô hình
        model_dir = os.path.join(settings.BASE_DIR, 'predictor', 'ai_engine')
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'football_model.pkl')
        joblib.dump(clf, model_path)

        self.stdout.write(self.style.SUCCESS(f"HOÀN TẤT! Đã lưu mô hình tại: {model_path}"))