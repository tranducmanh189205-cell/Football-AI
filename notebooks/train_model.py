import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestRegressor

# 1. TẠO DỮ LIỆU MẪU MỚI (Dự đoán số bàn thắng cụ thể)
np.random.seed(42)
n_matches = 1000

data = {
    'home_form': np.random.randint(1, 11, n_matches),
    'away_form': np.random.randint(1, 11, n_matches),
    'home_avg_goals': np.round(np.random.uniform(0.8, 3.2, n_matches), 2),
    'away_avg_goals': np.round(np.random.uniform(0.5, 2.8, n_matches), 2),
    'home_avg_conceded': np.round(np.random.uniform(0.5, 2.5, n_matches), 2),
    'away_avg_conceded': np.round(np.random.uniform(0.7, 2.8, n_matches), 2),
}
df = pd.DataFrame(data)

# Giả lập số bàn thắng thực tế dựa trên phong độ và hiệu suất
df['home_score'] = np.random.poisson(lam=np.clip(df['home_avg_goals'] * (df['home_form']/7), 0.5, 4))
df['away_score'] = np.random.poisson(lam=np.clip(df['away_avg_goals'] * (df['away_form']/7), 0.3, 3.5))

# 2. HUẤN LUYỆN 2 MÔ HÌNH REGRESSION (Dự đoán số lượng bàn thắng)
X = df[['home_form', 'away_form', 'home_avg_goals', 'away_avg_goals', 'home_avg_conceded', 'away_avg_conceded']]
y_home = df['home_score']
y_away = df['away_score']

model_home = RandomForestRegressor(n_estimators=100, random_state=42)
model_home.fit(X, y_home)

model_away = RandomForestRegressor(n_estimators=100, random_state=42)
model_away.fit(X, y_away)

# 3. LƯU CẢ 2 MODEL VÀO MỘT FILE DICTIONARY
os.makedirs('models', exist_ok=True)
bundle = {
    'model_home': model_home,
    'model_away': model_away
}
joblib.dump(bundle, 'models/football_score_model.pkl')
print("✅ Đã train và lưu mô hình dự đoán tỷ số thành công!")