# ⚽ Football AI – Hệ thống Dự đoán Kết quả Trận đấu Bóng đá bằng Machine Learning

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render%20Cloud-DA291C?style=for-the-badge)](https://football-ai-s9qo.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-EB4223?style=for-the-badge)](https://xgboost.readthedocs.io/)
[![TiDB Cloud](https://img.shields.io/badge/Database-TiDB%20Cloud%20(MySQL%208.0)-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://tidbcloud.com/)

> **Đồ án học phần Trí tuệ nhân tạo (AIP20202)**  
> **Sinh viên thực hiện:** Trần Đức Mạnh (MSSV: `2351220214` – Lớp `23CT4`)  
> **Giảng viên hướng dẫn:** TS. Đỗ Phúc Hảo  
> **Đơn vị:** Khoa Công nghệ Thông tin – Trường Đại học Kiến trúc Đà Nẵng

---

## 📌 1. Giới thiệu tổng quan

**Football AI** là hệ thống ứng dụng Học máy (Machine Learning) kết hợp nền tảng Web phân lớp 3 tầng để dự đoán xác suất kết quả trận đấu bóng đá (**Home Win – Draw – Away Win**) và tỷ số kỳ vọng tại **5 giải vô địch quốc gia hàng đầu châu Âu**:

| Mã giải | Tên giải đấu | Quốc gia | Dữ liệu lịch sử |
| :---: | :--- | :--- | :--- |
| `E0` | **Premier League** | Anh | Từ mùa giải 1993–1994 |
| `SP1` | **La Liga** | Tây Ban Nha | Từ mùa giải 1993–1994 |
| `I1` | **Serie A** | Ý | Từ mùa giải 1993–1994 |
| `D1` | **Bundesliga** | Đức | Từ mùa giải 1993–1994 |
| `F1` | **Ligue 1** | Pháp | Từ mùa giải 1993–1994 |

### ✨ Tính năng và điểm nhấn kỹ thuật
- **Không gian đặc trưng 7 chiều (Feature Engineering):** Trích xuất động chỉ số phong độ trượt 5 trận gần nhất ($F_{home}, F_{away}$), hiệu suất ghi bàn & thủng lưới trung bình 10 trận gần nhất ($G^{scored}, G^{conceded}$) và tỷ lệ thắng đối đầu lịch sử ($R_{h2h}$).
- **Giải thuật Khóa đồng bộ Logic Tỷ số – Xác suất:** Tự động hiệu chỉnh số bàn thắng dự kiến khớp 100% với nhãn xác suất cực đại ($H/D/A$), loại bỏ hoàn toàn nghịch lý dự đoán (ví dụ: dự đoán đội nhà thắng nhưng tỷ số lại là `1 - 2`).
- **Cơ chế dự đoán 3 chế độ linh hoạt:**
  - *Chế độ Tự động (Auto Mode):* Tự động quét cơ sở dữ liệu, tính toán chỉ số thực tế của hai đội và suy luận.
  - *Dự đoán nhanh 1-Click (Quick Predict):* Nhấn dự đoán trực tiếp từ danh sách lịch thi đấu theo vòng (*Matchday*) đồng bộ từ Football-Data.org API v4 (quy đổi múi giờ Việt Nam UTC+7).
  - *Chế độ Tùy chỉnh (Manual Mode):* Cho phép giả lập các thông số phong độ, bàn thắng, bàn thua để kiểm thử kịch bản.
- **Độ trễ phản hồi `< 150ms`:** Mô hình `.pkl` cùng bộ chuẩn hóa `StandardScaler` được nạp sẵn trên bộ nhớ RAM khi khởi động máy chủ, kết hợp giao tiếp bất đồng bộ **AJAX (Fetch API)** cập nhật giao diện *Glassmorphism Dark Mode* và bảng lịch sử dự đoán không cần tải lại trang.
- **Kiến trúc triển khai Cloud 24/7:** Tự động hóa CI/CD từ GitHub lên **Render Web Service** (`Gunicorn` + `WhiteNoise`) kết nối cơ sở dữ liệu phân tán **TiDB Cloud Serverless** qua giao thức bảo mật SSL/TLS.

---

## 🧠 2. Kiến trúc hệ thống & Thuật toán lõi

### 2.1. Luồng xử lý 5 khối chức năng
[Dữ liệu 5 giải đấu] ──▶ [Tiền xử lý & TiDB Cloud] ──▶ [Trích xuất Vector 7D] ──▶ [Mô hình AI & Khóa tỷ số] ──▶ [AJAX JSON / Web UI]
  (CSV & REST API)           (Chuẩn hóa 3NF)             (5-10 trận trượt)           (XGBoost .pkl)             (< 150ms)

### 2.2. Vector đặc trưng 7 chiều ($\mathbf{x} \in \mathbb{R}^7$)
Mỗi cặp đấu $(T_{home}, T_{away})$ trước giờ bóng lăn được chuyển hóa thành vector toán học 7 tham số:
$$\mathbf{x} = \begin{bmatrix} F_{home}, & F_{away}, & G_{home}^{scored}, & G_{away}^{scored}, & G_{home}^{conceded}, & G_{away}^{conceded}, & R_{h2h} \end{bmatrix}^T$$

- **Chỉ số phong độ chuẩn hóa ($F_{home}, F_{away} \in [2.0, 10.0]$):** Tính trên 5 trận chính thức gần nhất (Thắng = 3 điểm, Hòa = 1 điểm, Thua = 0 điểm):
  $$F = \min \left( 10.0, \max \left( 2.0, \frac{\sum_{i=1}^{5} \text{Points}_i}{15} \times 10.0 \right) \right)$$
- **Hiệu suất tấn công & phòng ngự ($G^{scored}, G^{conceded}$):** Trung bình bàn thắng ghi được và bàn thua phải nhận trong tối đa $N \le 10$ trận gần nhất.
- **Tỷ lệ đối đầu lịch sử ($R_{h2h} \in [0, 1]$):** Tỷ lệ chiến thắng của đội chủ nhà trên tổng số lần hai đội từng gặp nhau (gán mặc định `0.33` nếu chưa từng đối đầu để tránh giá trị rỗng).

### 2.3. Giải thuật Khóa đồng bộ Tỷ số – Xác suất
Từ phân phối xác suất đầu ra $[P_H, P_D, P_A]$ của mô hình AI, kỳ vọng bàn thắng sơ bộ được tính theo công thức:
$$\lambda_{home} = \left(0.55 \times G_{home}^{scored} + 0.45 \times G_{away}^{conceded}\right) \times \left(\frac{P_H}{40.0}\right)$$
$$\lambda_{away} = \left(0.55 \times G_{away}^{scored} + 0.45 \times G_{home}^{conceded}\right) \times \left(\frac{P_A}{40.0}\right)$$

Sau khi làm tròn $\hat{g}_{home} = \text{round}(\lambda_{home})$ và $\hat{g}_{away} = \text{round}(\lambda_{away})$, bộ khóa logic áp dụng ràng buộc:
- Nếu $P_H = \max(P_H, P_D, P_A)$ và $\hat{g}_{home} \le \hat{g}_{away} \implies \hat{g}_{home} = \hat{g}_{away} + 1$.
- Nếu $P_A = \max(P_H, P_D, P_A)$ và $\hat{g}_{away} \le \hat{g}_{home} \implies \hat{g}_{away} = \hat{g}_{home} + 1$.
- Nếu $P_D = \max(P_H, P_D, P_A) \implies \hat{g}_{home} = \hat{g}_{away}$.

---

## 🗄️ 3. Thiết kế Cơ sở dữ liệu (Chuẩn 3NF)

Hệ thống quản lý dữ liệu qua 4 bảng thực thể quan hệ trên **MySQL 8.0 / TiDB Cloud**:
- `predictor_league`: Lưu danh mục 5 giải đấu (`id`, `code`, `name`, `country`, `logo_url`).
- `predictor_team`: Lưu thông tin các câu lạc bộ thuộc từng giải (`id`, `league_id`, `name`, `logo_url`).
- `predictor_match`: Lưu trữ toàn bộ dữ liệu trận đấu lịch sử và lịch thi đấu sắp tới (`id`, `league_id`, `home_team_id`, `away_team_id`, `season`, `matchday`, `date`, `kickoff_time`, `home_score`, `away_score`, `result`, `status`).
- `predictor_history`: Lưu nhật ký các lượt dự đoán của người dùng qua AJAX (`id`, `home_team_id`, `away_team_id`, `predicted_home_goals`, `predicted_away_goals`, `predicted_result`, `mode`, `created_at`).

---

## 📊 4. Kết quả thực nghiệm & Đánh giá

Thực nghiệm được tiến hành trên **18.260 trận đấu** (10 mùa giải gần nhất của 5 giải đấu châu Âu), chia tập **Train (80%) – Test (20%)** theo đúng trục thời gian (*Time-series Split*) để chống rò rỉ dữ liệu tương lai (*Data Leakage*).

### 4.1. Đối sánh các thuật toán trên tập kiểm thử (3.652 trận)

| Mô hình Học máy | Accuracy | Precision (Macro) | Recall (Macro) | F1-Score (Macro) |
| :--- | :---: | :---: | :---: | :---: |
| Logistic Regression (Baseline) | 58.6% | 0.51 | 0.48 | 0.49 |
| Random Forest Classifier | 65.4% | 0.58 | 0.55 | 0.56 |
| **XGBoost Classifier (Tối ưu)** | **67.8%** | **0.61** | **0.58** | **0.59** |

### 4.2. Hiệu năng phân loại chi tiết theo nhãn (XGBoost)

| Nhãn kết quả | Precision | Recall | F1-Score | Số lượng mẫu thực tế |
| :--- | :---: | :---: | :---: | :---: |
| **H** (Đội nhà thắng) | 0.69 | 0.75 | 0.72 | 1.680 trận |
| **D** (Hòa) | 0.36 | 0.28 | 0.31 | 912 trận |
| **A** (Đội khách thắng) | 0.58 | 0.62 | 0.60 | 1.060 trận |

### 4.3. Mức độ đóng góp của 7 đặc trưng (Feature Importance)
1. `F_home` (Phong độ 5 trận gần nhất đội nhà): **21.4%**
2. `F_away` (Phong độ 5 trận gần nhất đội khách): **19.2%**
3. `G_home_scored` (Bàn thắng trung bình 10 trận đội nhà): **14.8%**
4. `G_away_scored` (Bàn thắng trung bình 10 trận đội khách): **13.5%**
5. `G_home_conceded` (Bàn thua trung bình 10 trận đội nhà): **11.2%**
6. `G_away_conceded` (Bàn thua trung bình 10 trận đội khách): **10.6%**
7. `R_h2h` (Tỷ lệ thắng đối đầu lịch sử): **9.3%**

---

## 📂 5. Cấu trúc thư mục dự án
---
Football-AI/
├── config/                 # Cấu hình lõi của dự án Django (settings.py, urls.py, wsgi.py)
├── datasets/               # Kho dữ liệu lịch sử CSV của 5 giải vô địch quốc gia châu Âu
├── models/                 # Mô hình học máy đã huấn luyện (.pkl) và bộ chuẩn hóa Scaler
├── notebooks/              # Jupyter Notebooks khám phá dữ liệu (EDA) & huấn luyện mô hình
├── predictor/              # Ứng dụng Django chính (models, views, feature_extractor, management/commands)
├── templates/              # Giao diện người dùng HTML5/CSS3 Glassmorphism Dark Mode
├── build.sh                # Tập lệnh tự động hóa CI/CD trên Render Cloud
├── data_dump.json          # Dữ liệu mẫu khởi tạo cơ sở dữ liệu
├── manage.py               # Trình quản lý dòng lệnh Django
└── requirements.txt        # Danh sách thư viện phụ thuộc Python

---

## ⚙️ 6. Hướng dẫn cài đặt và chạy trên Localhost

### Bước 1: Clone kho lưu trữ và kích hoạt môi trường ảo
git clone https://github.com/tranducmanh189205-cell/Football-AI.git
cd Football-AI
python -m venv venv

# Trên Windows:
venv\Scripts\activate
# Trên macOS / Linux:
source venv/bin/activate

### Bước 2: Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

### Bước 3: Khởi tạo cơ sở dữ liệu và nạp dữ liệu mẫu
python manage.py migrate
python manage.py loaddata data_dump.json

### Bước 4: Cập nhật dữ liệu trận đấu & lịch thi đấu (Tùy chọn)
python manage.py crawl_all_leagues
python manage.py sync_real_fixtures

### Bước 5: Khởi chạy máy chủ Web cục bộ
python manage.py runserver
# Truy cập trình duyệt tại: http://127.0.0.1:8000/

---

## 🌐 7. Liên kết hệ thống trực tuyến (Production)

- **Ứng dụng Web Cloud:** [https://football-ai-s9qo.onrender.com](https://football-ai-s9qo.onrender.com)
- **Mã nguồn GitHub:** [https://github.com/tranducmanh189205-cell/Football-AI](https://github.com/tranducmanh189205-cell/Football-AI)

*(Lưu ý: Hệ thống triển khai trên gói Render Free Tier nên có thể mất 40–50 giây khởi động nguội ở lần truy cập đầu tiên sau thời gian nghỉ).*
