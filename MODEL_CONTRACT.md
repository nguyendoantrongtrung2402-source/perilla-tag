# Hợp đồng model của Perilla Tag

File mô hình phải có tên **`model.joblib`** và đặt cùng thư mục với `app.py`.

## Feature đầu vào

Perilla Tag gửi đúng 6 feature theo thứ tự:

1. `R` — Mean R của toàn bộ pixel trong ROI
2. `G` — Mean G
3. `B` — Mean B
4. `Hue` — độ, 0–360
5. `Saturation` — %, 0–100
6. `Value` — %, 0–100

Vector:

```text
[R, G, B, Hue, Saturation, Value]
```

Model phải có hàm `predict()` tương thích kiểu scikit-learn.

## Nhãn đầu ra được chấp nhận

- `fresh` hoặc `0` → CÒN TƯƠI
- `transition` hoặc `1` → CHUYỂN TIẾP / CẦN DÙNG SỚM
- `spoiled` hoặc `2` → CÓ DẤU HIỆU HƯ HỎNG

Nếu model trả nhãn khác, app sẽ báo lỗi và **không tự đoán**.

## Lưu ý quan trọng

Khi huấn luyện model, phải dùng đúng cách tiền xử lý như app: ROI trung tâm 35%–65% theo cả chiều rộng và chiều cao, Mean RGB, rồi HSV từ Mean RGB. Nếu sau này đổi feature hoặc ROI, phải đổi đồng thời cả bước tạo dữ liệu huấn luyện và app dự đoán.
