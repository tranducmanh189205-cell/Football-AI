import os
import joblib
import pandas as pd

# Đường dẫn trỏ tới file mô hình đã train (.pkl) nằm trong thư mục models/
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "football_score_model.pkl")

def predict_match(home_form, away_form, home_avg_goals, away_avg_goals, home_avg_conceded, away_avg_conceded):
    """
    Hàm nhận các chỉ số thống kê của 2 đội, load mô hình AI từ file .pkl 
    và trả về dự đoán tỷ số cùng kết quả trận đấu.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Không tìm thấy file mô hình tại đường dẫn: {MODEL_PATH}")

    # Load bộ mô hình (chứa model dự đoán bàn thắng đội nhà và đội khách)
    bundle = joblib.load(MODEL_PATH)
    model_home = bundle['model_home']
    model_away = bundle['model_away']

    # Tạo DataFrame đầu vào đúng tên các cột mà lúc train model đã sử dụng
    input_data = pd.DataFrame([[
        home_form, away_form, home_avg_goals, away_avg_goals, home_avg_conceded, away_avg_conceded
    ]], columns=[
        'home_form', 'away_form', 'home_avg_goals', 'away_avg_goals', 'home_avg_conceded', 'away_avg_conceded'
    ])

    # Dự đoán số bàn thắng (dạng float, sau đó làm tròn thành số nguyên)
    predicted_home_goals = round(float(model_home.predict(input_data)[0]))
    predicted_away_goals = round(float(model_away.predict(input_data)[0]))

    # Đảm bảo số bàn thắng không bị âm
    predicted_home_goals = max(0, predicted_home_goals)
    predicted_away_goals = max(0, predicted_away_goals)

    # Xác định kết quả thắng/thua/hòa dựa trên tỷ số dự đoán
    # H = Home win, A = Away win, D = Draw
    if predicted_home_goals > predicted_away_goals:
        prediction = 'H'
    elif predicted_home_goals < predicted_away_goals:
        prediction = 'A'
    else:
        prediction = 'D'

    score_result = f"{predicted_home_goals} - {predicted_away_goals}"
    
    return prediction, score_result, predicted_home_goals, predicted_away_goals