from ml_model import predict_match


# Trận đấu giả lập
prediction, probabilities = predict_match(
    home_form=8,
    away_form=6,
    home_goals=3,
    away_goals=1
)


print("===== KẾT QUẢ AI =====")

print("Dự đoán:", prediction)

print("\nXác suất:")

for result, probability in probabilities.items():
    print(
        f"{result}: {probability}%"
    )