import pandas as pd

# Đọc dữ liệu
df = pd.read_csv("datasets/matches.csv")

# Hiển thị toàn bộ dữ liệu
print("===== DỮ LIỆU =====")
print(df)

# Hiển thị tên các cột
print("\n===== CÁC CỘT =====")
print(df.columns.tolist())

# Hiển thị kích thước dữ liệu
print("\n===== KÍCH THƯỚC =====")
print("Số dòng:", df.shape[0])
print("Số cột:", df.shape[1])

# Kiểm tra dữ liệu bị thiếu
print("\n===== DỮ LIỆU BỊ THIẾU =====")
print(df.isnull().sum())

# Thống kê kết quả
print("\n===== SỐ LƯỢNG KẾT QUẢ =====")
print(df["result"].value_counts())