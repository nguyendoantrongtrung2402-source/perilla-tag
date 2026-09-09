# Perilla Tag

**MÀU THAY ĐỔI. TƯƠI HAY THỐI?**  
*Chụp thẻ. Perilla Tag đọc màu.*

Perilla Tag là web Streamlit dành cho dự án KHKT về thẻ chỉ thị màu tía tô. Phiên bản hiện tại hoàn thiện camera, chọn ảnh, ROI tự động, Mean RGB, HSV/Hue, HEX và giao diện kỹ thuật. **Chưa có `model.joblib`, nên app tuyệt đối không giả lập kết quả tươi/hư.**

---

## 1. Perilla Tag hoạt động như thế nào?

Luồng hiện tại:

```text
Mở web
→ Chụp thẻ hoặc Chọn ảnh
→ thẻ nằm trong vùng giữa
→ app cắt ROI trung tâm
→ tính Mean RGB
→ đổi sang Hue / Saturation / Value
→ kiểm tra model.joblib
→ chưa có model: báo “CHƯA CÓ MÔ HÌNH THỰC NGHIỆM”
```

Sau này:

```text
Ảnh → ROI → RGB + HSV → model.joblib → 1 trong 3 trạng thái
```

Ba trạng thái model được phép trả về:

- CÒN TƯƠI
- CHUYỂN TIẾP / CẦN DÙNG SỚM
- CÓ DẤU HIỆU HƯ HỎNG

App không hiển thị “% độ tươi”.

---

## 2. Vì sao dùng Streamlit?

Streamlit dùng Python nên dễ nối với `model.joblib` sau khi có dữ liệu thí nghiệm. App vẫn có thể tạo giao diện web và đưa lên Streamlit Community Cloud để mở trên điện thoại.

Bản này dùng **Streamlit Components V2** để tạo camera riêng có khung giữa, không cần thêm thư viện JavaScript bên ngoài.

---

## 3. Cấu trúc folder

```text
perilla-tag/
├── app.py
├── perilla_core.py
├── requirements.txt
├── MODEL_CONTRACT.md
├── self_test.py
├── README.md
└── .streamlit/
    └── config.toml
```

Sau này chỉ thêm:

```text
model.joblib
```

vào cùng chỗ với `app.py`.

---

## 4. Tạo folder và file

Nếu bạn tải nguyên folder/ZIP đã được tạo thì **không cần tự tạo từng file**. Chỉ giải nén ra một folder, ví dụ:

```text
Desktop/perilla-tag
```

- `app.py`: giao diện, camera, upload, kết quả.
- `perilla_core.py`: ROI, RGB, HSV và logic model.
- `requirements.txt`: danh sách thư viện Python.
- `.streamlit/config.toml`: màu giao diện Streamlit.
- `MODEL_CONTRACT.md`: quy tắc để model sau này tương thích.
- `self_test.py`: kiểm tra phần tính màu bằng ảnh kỹ thuật số #808080.

**File extension** là phần sau dấu chấm, ví dụ `.py`, `.txt`, `.toml`.

---

## 5. Cài Python và thư viện

### Nếu máy chưa có Python

Cài Python 3.12 hoặc một bản Python đang được Streamlit hỗ trợ. Khi cài trên Windows, nhớ chọn tùy chọn thêm Python vào PATH nếu trình cài đặt có hỏi.

### Mở Command Prompt

Trên Windows:

1. Nhấn nút Start.
2. Gõ `cmd`.
3. Mở **Command Prompt**.

`Terminal`/`Command Prompt` là cửa sổ cho phép gõ lệnh.

### Đi vào folder dự án

Ví dụ nếu folder ở Desktop:

```bat
cd %USERPROFILE%\Desktop\perilla-tag
```

### Tạo môi trường riêng (khuyên dùng)

```bat
python -m venv .venv
```

Bật môi trường:

```bat
.venv\Scripts\activate
```

### Cài thư viện

```bat
python -m pip install -r requirements.txt
```

`pip` là công cụ cài thư viện Python.

---

## 6. Chạy app trên máy

Trong Command Prompt, đang đứng ở folder `perilla-tag`, chạy:

```bat
streamlit run app.py
```

Nếu lệnh `streamlit` không nhận, dùng:

```bat
python -m streamlit run app.py
```

Trình duyệt sẽ mở địa chỉ dạng:

```text
http://localhost:8501
```

`localhost` nghĩa là web đang chạy trên chính máy của bạn.

---

## 7. Test phần xử lý màu trước

Không cần mở web, có thể chạy:

```bat
python self_test.py
```

Kết quả đúng phải bắt đầu bằng:

```text
PASS — ROI, Mean RGB, HSV và HEX hoạt động đúng với ảnh #808080.
```

Ảnh số #808080 có RGB = 128,128,128 nên bài test kiểm tra được phần tính màu cơ bản.

---

## 8. Test “Chọn ảnh”

1. Mở app.
2. Chọn **▣ Chọn ảnh**.
3. Chọn JPG/JPEG/PNG/WEBP.
4. Đảm bảo thẻ nằm gần chính giữa ảnh.
5. App sẽ tự phân tích.
6. Vì chưa có model, kết quả phải là:

```text
CHƯA CÓ MÔ HÌNH THỰC NGHIỆM
```

7. Mở **Xem chi tiết kỹ thuật** để xem Mean R/G/B, Hue, Saturation, Value, HEX, ROI và ảnh crop.

---

## 9. Test camera

1. Chọn **📷 Chụp thẻ**.
2. Bấm **Bật camera**.
3. Cho phép trình duyệt sử dụng camera.
4. Trên điện thoại, hệ thống ưu tiên camera sau.
5. Đưa thẻ vào khung giữa.
6. Bấm nút chụp tròn.
7. App phân tích ảnh vừa chụp.

Nếu mở trong Zalo/Facebook/Instagram/Messenger và camera lỗi, hãy mở link bằng Chrome hoặc Safari.

Camera web cần môi trường an toàn. `localhost` được trình duyệt coi là phù hợp khi thử trên chính máy; khi mở từ Internet nên dùng HTTPS. Streamlit Community Cloud cung cấp link HTTPS.

---

## 10. ROI của app

ROI mặc định là vùng giữa:

```text
x: 35% → 65% chiều rộng
Y: 35% → 65% chiều cao
```

Camera hiển thị đúng khung này. Ảnh upload cũng dùng cùng tỷ lệ.

App tính màu từ **ảnh thật đã đọc**, không từ thumbnail hiển thị trên màn hình.

---

## 11. Thêm model.joblib sau này

Sau khi có dữ liệu thực nghiệm và huấn luyện model:

1. Đặt file có đúng tên:

```text
model.joblib
```

2. Đặt cạnh `app.py`:

```text
perilla-tag/
├── app.py
├── model.joblib
└── ...
```

3. Chạy lại app.

Model phải nhận đúng 6 feature theo thứ tự:

```text
[R, G, B, Hue, Saturation, Value]
```

Nhãn được chấp nhận:

```text
fresh / 0
transition / 1
spoiled / 2
```

Xem chi tiết trong `MODEL_CONTRACT.md`.

> Khi huấn luyện model thật, nên dùng cùng phiên bản scikit-learn giữa máy huấn luyện và app deploy. Nếu cần, sau này khóa phiên bản đó trong `requirements.txt`.

---

## 12. Deploy lên Streamlit Community Cloud

### A. Chuẩn bị GitHub

Bạn cần tài khoản GitHub.

1. Đăng nhập GitHub.
2. Tạo repository mới, ví dụ `perilla-tag`.
3. Có thể để repository **Public** cho dễ triển khai.
4. Chọn **Add file → Upload files**.
5. Upload:
   - `app.py`
   - `perilla_core.py`
   - `requirements.txt`
   - `MODEL_CONTRACT.md`
   - `self_test.py`
   - `README.md`
   - folder `.streamlit/config.toml`
6. Chưa có `model.joblib` **không sao**. App đã được viết để chạy mà không cần model.
7. Commit các file.

### B. Deploy

1. Mở Streamlit Community Cloud.
2. Đăng nhập/kết nối bằng GitHub.
3. Chọn **Create app**.
4. Chọn repository `perilla-tag`.
5. Chọn branch chính, thường là `main`.
6. Entrypoint/file chạy chính là:

```text
app.py
```

7. Bấm **Deploy**.
8. Khi xong, bạn nhận link dạng `...streamlit.app`.
9. Mở link bằng Chrome/Safari trên điện thoại.
10. Bấm **Bật camera** và cấp quyền camera.

Sau này khi thêm `model.joblib` vào repository, Streamlit Community Cloud sẽ cập nhật app từ GitHub.

---

## 13. Lỗi thường gặp

### “Không mở được camera”

- Kiểm tra đã cấp quyền camera chưa.
- Đóng app khác đang dùng camera.
- Thử Chrome/Safari.
- Nếu đang mở trong Zalo/Facebook/Instagram/Messenger, mở link bằng trình duyệt ngoài.

### “Camera web cần HTTPS”

- Trên máy: chạy bằng `localhost`.
- Trên điện thoại/Internet: dùng bản Streamlit Community Cloud.

### “CHƯA CÓ MÔ HÌNH THỰC NGHIỆM”

Đây **không phải lỗi**. Đây là trạng thái đúng trước khi bạn có dữ liệu và `model.joblib`.

### “Model chưa sẵn sàng”

- Kiểm tra tên file phải là `model.joblib`.
- Kiểm tra model có `predict()`.
- Kiểm tra model nhận 6 feature.
- Nếu model được lưu bằng scikit-learn phiên bản khác, cài cùng phiên bản.

### “Đầu ra của mô hình không đúng định dạng”

Model phải trả `fresh`, `transition`, `spoiled` hoặc số `0`, `1`, `2`.

### Ảnh upload đọc màu sai vùng

Ảnh phải có thẻ nằm gần giữa. ROI tự động không phải AI tìm vật thể; nó lấy vùng giữa cố định theo khung hướng dẫn.

---

## 14. Checklist cuối

- [ ] `python self_test.py` báo PASS.
- [ ] `streamlit run app.py` mở được web.
- [ ] Giao diện hiển thị tốt trên điện thoại/laptop.
- [ ] Chọn ảnh JPG/PNG được.
- [ ] Camera xin quyền đúng.
- [ ] Camera ưu tiên phía sau trên điện thoại.
- [ ] Có khung “Đặt thẻ vào trong khung”.
- [ ] ROI tự động ở giữa.
- [ ] Mean RGB hiển thị trong chi tiết kỹ thuật.
- [ ] Hue/Saturation/Value và HEX hiển thị.
- [ ] Khi chưa có model, app không giả dự đoán.
- [ ] Có cảnh báo giới hạn khoa học ở cuối trang.
- [ ] Khi có model, model nhận `[R,G,B,Hue,Saturation,Value]`.
- [ ] Model chỉ trả 1 trong 3 nhãn đã quy định.
- [ ] Deploy Streamlit Community Cloud mở được bằng HTTPS.

---

## 15. Giới hạn khoa học

Perilla Tag không phải thiết bị chứng nhận an toàn thực phẩm. Dòng cảnh báo cố định của app là:

> Kết quả mang tính hỗ trợ nhận định trong điều kiện thử nghiệm của đề tài và không thay thế kiểm nghiệm an toàn thực phẩm.
