# Perilla Tag

Perilla Tag là web Streamlit dùng trong đề tài KHKT về thẻ chỉ thị màu tía tô. Bản này ưu tiên trải nghiệm trên điện thoại: hero gọn, hai lựa chọn **Chụp thẻ / Chọn ảnh** cân nhau, camera giữ khung ổn định và kết quả hiển thị bằng card.

## Luồng xử lý hiện tại

```text
Ảnh camera / ảnh tải lên
→ ROI trung tâm 35%–65% theo chiều rộng và chiều cao
→ Mean RGB
→ Hue / Saturation / Value
→ HEX
→ kiểm tra model.joblib
```

Khi **chưa có `model.joblib`**, app vẫn xử lý ảnh và trích màu nhưng chỉ hiển thị **CHƯA CÓ MÔ HÌNH THỰC NGHIỆM**. App không tự đặt ngưỡng, không tạo model giả và không tự đoán tươi/hư.

Khi có model thật, card kết quả tự đổi màu:

- `fresh` / `0` → **CÒN TƯƠI** → xanh
- `transition` / `1` → **CHUYỂN TIẾP / CẦN DÙNG SỚM** → cam/vàng
- `spoiled` / `2` → **CÓ DẤU HIỆU HƯ HỎNG** → đỏ

Trạng thái chưa có model dùng card tím/trung tính.

## Cấu trúc repository

```text
perilla-tag/
├── app.py
├── perilla_core.py
├── requirements.txt
├── README.md
├── MODEL_CONTRACT.md
└── .streamlit/
    └── config.toml
```

Không cần thư mục `assets`, `.venv`, `__pycache__`, file backup hay file test giao diện.

## Deploy lên Streamlit Community Cloud

1. Upload toàn bộ các file/thư mục ở trên vào repository GitHub.
2. Tạo app trên Streamlit Community Cloud từ repository đó.
3. Chọn branch `main`.
4. Main file path: `app.py`.
5. Deploy và mở link HTTPS trên điện thoại.
6. Cấp quyền camera khi trình duyệt hỏi.

Sau này chỉ cần thêm `model.joblib` vào **cùng thư mục với `app.py`** rồi commit lên GitHub. Streamlit sẽ cập nhật app.

## Yêu cầu model

Model phải nhận đúng 6 feature theo thứ tự:

```text
[R, G, B, Hue, Saturation, Value]
```

Chi tiết xem `MODEL_CONTRACT.md`.

## Lưu ý khoa học

Kết quả mang tính hỗ trợ nhận định trong điều kiện thử nghiệm của đề tài và không thay thế kiểm nghiệm an toàn thực phẩm.
