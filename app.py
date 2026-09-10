from __future__ import annotations

import base64
import io
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

from perilla_core import (
    FEATURE_SCHEMA,
    ROI_NORMALIZED,
    analyze_color,
    crop_indicator_roi,
    load_model,
    normalize_image,
    predict_state,
)

APP_DIR = Path(__file__).resolve().parent
MODEL_PATH = APP_DIR / "model.joblib"
BOTANICAL_PATH = APP_DIR / "assets" / "perilla_botanical.png"
LEAVES_PATH = APP_DIR / "assets" / "perilla_leaves.png"

st.set_page_config(
    page_title="Perilla Tag",
    page_icon="🍃",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def image_data_uri(path: Path) -> str:
    """Đưa asset PNG vào HTML/CSS để deploy không cần đường dẫn public riêng."""
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


BOTANICAL_DATA_URI = image_data_uri(BOTANICAL_PATH)
LEAVES_DATA_URI = image_data_uri(LEAVES_PATH)

# -----------------------------
# UI / UX
# Chỉ là lớp hiển thị. Không tác động xử lý ảnh, ROI hay model.
# -----------------------------
UI_HTML = r"""
<style>
:root {
  --pt-bg: #09050d;
  --pt-bg-soft: #14091b;
  --pt-text: #fbf8fc;
  --pt-muted: #bdaec5;
  --pt-purple: #b777cf;
  --pt-purple-soft: #d9bae6;
  --pt-border: rgba(225, 203, 236, .18);
}

html, body { background: var(--pt-bg); }

[data-testid="stAppViewContainer"] {
  position: relative;
  isolation: isolate;
  overflow-x: hidden;
  color: var(--pt-text);
  background:
    radial-gradient(ellipse at 18% -8%, rgba(119, 61, 139, .20), transparent 32%),
    radial-gradient(ellipse at 93% 18%, rgba(96, 44, 114, .11), transparent 27%),
    linear-gradient(180deg, #170a1d 0%, #0c0711 36%, #07040a 100%);
  background-attachment: fixed;
}

/* Watermark botanical ở hai rìa; phần giữa để sạch */
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
  content: "";
  position: fixed;
  pointer-events: none;
  z-index: 0;
  background: url("__BOTANICAL__") center / contain no-repeat;
  filter: invert(1);
  mix-blend-mode: screen;
}

[data-testid="stAppViewContainer"]::before {
  width: 300px;
  height: 420px;
  right: -120px;
  top: 210px;
  opacity: .045;
  transform: rotate(-8deg);
}

[data-testid="stAppViewContainer"]::after {
  width: 270px;
  height: 390px;
  left: -130px;
  bottom: -85px;
  opacity: .038;
  transform: rotate(158deg);
}

[data-testid="stMain"], .stMain, .block-container { position: relative; z-index: 1; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: .45rem; }
#MainMenu { visibility: hidden; }

.block-container {
  max-width: 980px;
  padding-top: 1rem;
  padding-bottom: 2.8rem;
}

/* HERO: bám bố cục mẫu - chữ trái, lá line-art phải */
.pt-hero {
  position: relative;
  overflow: hidden;
  min-height: 365px;
  margin: 0 0 30px;
  padding: 45px 48px 40px;
  border: 1px solid rgba(231, 208, 241, .23);
  border-radius: 30px;
  background:
    radial-gradient(circle at 16% 14%, rgba(133, 73, 154, .14), transparent 31%),
    radial-gradient(circle at 90% 12%, rgba(133, 73, 154, .11), transparent 27%),
    linear-gradient(135deg, rgba(47, 27, 58, .98) 0%, rgba(25, 15, 32, .99) 56%, rgba(14, 9, 18, 1) 100%);
  box-shadow: 0 28px 80px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.03);
}

.pt-hero::before,
.pt-hero::after {
  content: "";
  position: absolute;
  pointer-events: none;
  border: 1px solid rgba(226, 198, 239, .10);
  border-radius: 50%;
}

.pt-hero::before {
  width: 370px;
  height: 370px;
  right: -190px;
  top: 125px;
}
.pt-hero::after {
  width: 520px;
  height: 520px;
  right: -320px;
  bottom: -360px;
}

.pt-hero-copy {
  position: relative;
  z-index: 4;
  width: 62%;
  max-width: 610px;
}

.pt-eyebrow {
  margin-bottom: 1.15rem;
  color: #e2c9ec;
  font-size: .84rem;
  font-weight: 850;
  letter-spacing: .30em;
}

.pt-title {
  margin: 0 0 1.05rem;
  color: #fff;
  font-size: clamp(3rem, 6vw, 5.15rem);
  font-weight: 950;
  line-height: .98;
  letter-spacing: -.045em;
}
.pt-title-line { display: block; white-space: nowrap; }

.pt-slogan {
  margin: 0 0 .72rem;
  color: #f8f3fa;
  font-size: 1.22rem;
  font-weight: 830;
}

.pt-sub {
  margin: 0;
  max-width: 38ch;
  color: var(--pt-muted);
  font-size: 1rem;
  line-height: 1.56;
}

.pt-hero-art {
  position: absolute;
  z-index: 2;
  right: 22px;
  top: 16px;
  width: 39%;
  height: 90%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  pointer-events: none;
  overflow: hidden;
}

.pt-hero-art img {
  width: 118%;
  max-width: none;
  height: auto;
  object-fit: contain;
  opacity: .16;
  filter: invert(1) drop-shadow(0 0 16px rgba(190,130,211,.10));
  mix-blend-mode: screen;
  transform: rotate(-6deg) translate(10px, -2px);
}

.pt-hero-dots {
  position: absolute;
  z-index: 4;
  right: 34px;
  top: 52%;
  display: grid;
  gap: 8px;
}
.pt-hero-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(224, 197, 236, .30);
}

/* Nội dung dưới hero tối giản, không thêm họa tiết */
.pt-section {
  margin: 0 0 .7rem;
  padding-top: .18rem;
}
.pt-section-kicker {
  margin-bottom: .28rem;
  color: #c999d9;
  font-size: .70rem;
  letter-spacing: .18em;
  font-weight: 850;
  text-transform: uppercase;
}
.pt-section-title {
  margin: 0 0 .2rem;
  color: var(--pt-text);
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: -.025em;
}
.pt-section-sub {
  margin: 0;
  max-width: 58ch;
  color: var(--pt-muted);
  font-size: .92rem;
  line-height: 1.5;
}

/* Hai lựa chọn giữ logic radio nhưng nhìn như segmented control */
div[role="radiogroup"] { gap: .6rem; margin-top: .8rem; margin-bottom: .4rem; }
div[role="radiogroup"] label {
  min-height: 52px;
  padding: .68rem 1rem;
  border: 1px solid rgba(229,205,239,.16);
  border-radius: 15px;
  background: rgba(30,20,37,.70);
  display: flex !important;
  align-items: center;
  justify-content: center;
  transition: .14s ease;
}
div[role="radiogroup"] label:hover {
  background: rgba(45,27,55,.84);
  border-color: rgba(223,190,237,.27);
}
div[role="radiogroup"] label[data-checked="true"] {
  background: linear-gradient(145deg, rgba(112,62,130,.94), rgba(76,41,90,.96));
  border-color: rgba(225,195,239,.30);
  box-shadow: 0 10px 26px rgba(85,44,100,.18);
}

.pt-note {
  margin: .7rem 0 .8rem;
  color: #a999b1;
  font-size: .84rem;
  line-height: 1.45;
}

[data-testid="stFileUploader"] {
  border: 1px dashed rgba(218,184,233,.27);
  border-radius: 16px;
  background: rgba(24,16,30,.55);
}

[data-testid="stExpander"] {
  border: 1px solid rgba(225,203,236,.14);
  border-radius: 17px;
  background: rgba(20,13,25,.70);
}

[data-testid="stMetric"] {
  border: 1px solid rgba(225,203,236,.10);
  border-radius: 15px;
  background: rgba(30,20,37,.65);
  padding: .45rem .65rem;
}

.pt-footer {
  margin-top: 1.8rem;
  padding-top: .9rem;
  border-top: 1px solid rgba(225,203,236,.11);
  color: #9f91a6;
  text-align: center;
  font-size: .77rem;
  line-height: 1.5;
}

@media (max-width: 760px) {
  .block-container { padding-left: .9rem; padding-right: .9rem; padding-top: .65rem; }
  .pt-hero { min-height: 330px; padding: 28px 22px 26px; border-radius: 24px; }
  .pt-hero-copy { width: 69%; }
  .pt-title { font-size: clamp(2.15rem, 10.5vw, 3.45rem); }
  .pt-slogan { font-size: 1rem; }
  .pt-sub { font-size: .86rem; max-width: 30ch; }
  .pt-hero-art { width: 43%; right: -8px; opacity: .88; }
  .pt-hero-art img { width: 132%; opacity: .13; }
  .pt-hero-dots { display: none; }
  [data-testid="stAppViewContainer"]::before { width: 210px; height: 310px; right: -110px; top: 290px; }
  [data-testid="stAppViewContainer"]::after { width: 210px; height: 300px; left: -120px; bottom: -60px; }
}
</style>

<div class="pt-hero">
  <div class="pt-hero-copy">
    <div class="pt-eyebrow">PERILLA TAG</div>
    <div class="pt-title">
      <span class="pt-title-line">MÀU THAY ĐỔI.</span>
      <span class="pt-title-line">TƯƠI HAY THỐI?</span>
    </div>
    <div class="pt-slogan">Chụp thẻ. Perilla Tag đọc màu.</div>
    <p class="pt-sub">Đặt thẻ vào khung giữa, chụp hoặc chọn ảnh, rồi để hệ thống đọc màu của thẻ.</p>
  </div>
  <div class="pt-hero-art" aria-hidden="true">
    <img src="__LEAVES__" alt="">
  </div>
  <div class="pt-hero-dots" aria-hidden="true"><i></i><i></i><i></i></div>
</div>

<div class="pt-section">
  <div class="pt-section-title">Quét thẻ</div>
  <p class="pt-section-sub">Chụp trực tiếp hoặc chọn ảnh có sẵn. Đặt vùng màu của thẻ vào chính giữa để Perilla Tag tự lấy ROI.</p>
</div>
"""

ui_rendered = UI_HTML.replace("__BOTANICAL__", BOTANICAL_DATA_URI).replace("__LEAVES__", LEAVES_DATA_URI)
st.html(ui_rendered)

# -----------------------------
# Camera component V2 (không cần thư viện JS ngoài)
# -----------------------------
CAMERA_HTML = """
<div class="pt-camera-shell">
  <div class="pt-cam-topline">
    <span class="pt-dot"></span>
    <span>Camera thẻ chỉ thị</span>
  </div>
  <div class="pt-browser-warning" hidden></div>
  <div class="pt-stage">
    <video class="pt-video" autoplay playsinline muted></video>
    <canvas class="pt-canvas" hidden></canvas>
    <div class="pt-guide" aria-hidden="true">
      <span class="c tl"></span><span class="c tr"></span>
      <span class="c bl"></span><span class="c br"></span>
      <div class="pt-guide-label">Đặt thẻ vào trong khung</div>
    </div>
    <div class="pt-idle">
      <div class="pt-cam-icon">◉</div>
      <div>Nhấn “Bật camera” để bắt đầu</div>
    </div>
  </div>
  <div class="pt-cam-status">Camera chưa bật.</div>
  <div class="pt-cam-actions">
    <button class="pt-start" type="button">Bật camera</button>
    <button class="pt-shot" type="button" disabled aria-label="Chụp thẻ"><span></span></button>
  </div>
  <button class="pt-copy" type="button" hidden>Sao chép liên kết</button>
</div>
"""

CAMERA_CSS = """
.pt-camera-shell {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 0;
  border: 0;
  background: transparent;
  color: #f7f2f9;
  font-family: var(--st-font);
}

.pt-cam-topline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 9px 2px;
  color: #bfaec8;
  font-size: 12px;
  font-weight: 760;
  letter-spacing: .02em;
}

.pt-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #bf75d9;
  box-shadow: 0 0 13px rgba(191,117,217,.62);
}

.pt-browser-warning {
  margin: 0 0 10px;
  padding: 11px 12px;
  border: 1px solid rgba(235,172,89,.22);
  border-radius: 14px;
  background: rgba(119,72,31,.24);
  color: #f2d8b7;
  font-size: 12px;
  line-height: 1.42;
}

.pt-stage {
  width: 100%;
  position: relative;
  overflow: hidden;
  aspect-ratio: 4/3;
  border: 1px solid rgba(223, 194, 236, .16);
  border-radius: 25px;
  background: #050407;
  box-shadow: 0 24px 62px rgba(0,0,0,.30);
}

.pt-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  background: #050407;
}

.pt-idle {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 20px;
  color: #a999b1;
  text-align: center;
}

.pt-cam-icon {
  color: #bf83d3;
  font-size: 34px;
}

.pt-guide {
  position: absolute;
  z-index: 4;
  left: 35%;
  top: 35%;
  width: 30%;
  height: 30%;
  pointer-events: none;
}

.pt-guide::before {
  content: "";
  position: absolute;
  inset: 0;
  border: 1px solid rgba(255,255,255,.31);
  border-radius: 14px;
  background: rgba(255,255,255,.015);
  box-shadow: 0 0 0 999px rgba(0,0,0,.21);
}

.pt-guide-label {
  position: absolute;
  left: 50%;
  bottom: -32px;
  transform: translateX(-50%);
  white-space: nowrap;
  padding: 5px 9px;
  border: 1px solid rgba(255,255,255,.07);
  border-radius: 999px;
  background: rgba(8,5,10,.76);
  color: #f1e8f4;
  font-size: 11px;
}

.c {
  position: absolute;
  z-index: 5;
  width: 20px;
  height: 20px;
  border-color: #f2e1f8;
  border-style: solid;
  filter: drop-shadow(0 0 7px rgba(214,170,232,.19));
}
.tl { left:-1px; top:-1px; border-width:3px 0 0 3px; border-radius:8px 0 0 0; }
.tr { right:-1px; top:-1px; border-width:3px 3px 0 0; border-radius:0 8px 0 0; }
.bl { left:-1px; bottom:-1px; border-width:0 0 3px 3px; border-radius:0 0 0 8px; }
.br { right:-1px; bottom:-1px; border-width:0 3px 3px 0; border-radius:0 0 8px 0; }

.pt-cam-status {
  min-height: 19px;
  margin: 10px 3px 2px;
  color: #a897b1;
  font-size: 12px;
  line-height: 1.35;
}

.pt-cam-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 7px;
}

.pt-start,
.pt-copy {
  padding: 10px 14px;
  border: 1px solid rgba(222,190,236,.18);
  border-radius: 13px;
  background: rgba(61, 37, 72, .86);
  color: #fff;
  font-weight: 780;
  cursor: pointer;
}

.pt-start:hover,
.pt-copy:hover {
  background: rgba(79, 45, 94, .94);
}

.pt-shot {
  width: 72px;
  height: 72px;
  display: grid;
  place-items: center;
  padding: 5px;
  border: 3px solid rgba(255,255,255,.96);
  border-radius: 50%;
  background: rgba(255,255,255,.018);
  cursor: pointer;
  box-shadow: 0 11px 28px rgba(0,0,0,.24);
}

.pt-shot span {
  width: 51px;
  height: 51px;
  display: block;
  border-radius: 50%;
  background: #fff;
  transition: transform .12s ease;
}

.pt-shot:not(:disabled):active span {
  transform: scale(.88);
}

.pt-shot:disabled {
  opacity: .28;
  cursor: not-allowed;
}

.pt-copy {
  display: block;
  margin: 8px auto 0;
  font-size: 12px;
}

@media (max-width: 640px) {
  .pt-stage { border-radius: 21px; }
}
"""

CAMERA_JS = r"""
export default function({ parentElement, setStateValue }) {
  if (parentElement.__perillaReady) return;
  parentElement.__perillaReady = true;

  const video = parentElement.querySelector('.pt-video');
  const canvas = parentElement.querySelector('.pt-canvas');
  const stage = parentElement.querySelector('.pt-stage');
  const idle = parentElement.querySelector('.pt-idle');
  const startBtn = parentElement.querySelector('.pt-start');
  const shotBtn = parentElement.querySelector('.pt-shot');
  const status = parentElement.querySelector('.pt-cam-status');
  const warning = parentElement.querySelector('.pt-browser-warning');
  const copyBtn = parentElement.querySelector('.pt-copy');
  let stream = null;

  const ua = navigator.userAgent || '';
  const inApp = /FBAN|FBAV|Instagram|Line\/|Zalo|Messenger/i.test(ua);
  if (inApp) {
    warning.hidden = false;
    warning.textContent = 'Bạn đang mở trong trình duyệt nhúng. Nếu camera không chạy, hãy mở Perilla Tag bằng Chrome hoặc Safari.';
    copyBtn.hidden = false;
  }
  if (!window.isSecureContext && location.hostname !== 'localhost') {
    warning.hidden = false;
    warning.textContent = 'Camera web cần kết nối an toàn HTTPS. Hãy dùng bản đã deploy hoặc mở trên localhost.';
  }

  async function stopCamera() {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }
    shotBtn.disabled = true;
  }

  function friendlyError(err) {
    if (!err) return 'Không mở được camera. Hãy thử lại.';
    if (err.name === 'NotAllowedError' || err.name === 'SecurityError') return 'Bạn chưa cho phép dùng camera. Hãy cấp quyền camera rồi thử lại.';
    if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') return 'Không tìm thấy camera trên thiết bị.';
    if (err.name === 'NotReadableError' || err.name === 'TrackStartError') return 'Camera có thể đang được ứng dụng khác sử dụng. Hãy đóng ứng dụng đó rồi thử lại.';
    if (err.name === 'OverconstrainedError') return 'Camera không hỗ trợ cấu hình yêu cầu. Hãy thử lại.';
    return 'Không mở được camera. Hãy thử bằng Chrome/Safari và kiểm tra quyền camera.';
  }

  async function startCamera() {
    await stopCamera();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      status.textContent = 'Trình duyệt này không hỗ trợ camera web. Hãy dùng Chrome hoặc Safari.';
      return;
    }
    startBtn.disabled = true;
    startBtn.textContent = 'Đang mở…';
    status.textContent = 'Đang xin quyền camera…';
    try {
      const constraints = {
        audio: false,
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280, max: 1920 },
          height: { ideal: 960, max: 1440 }
        }
      };
      stream = await navigator.mediaDevices.getUserMedia(constraints);
      video.srcObject = stream;
      await video.play();
      if (video.videoWidth && video.videoHeight) {
        stage.style.aspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
      }
      idle.style.display = 'none';
      shotBtn.disabled = false;
      status.textContent = 'Camera đã sẵn sàng. Đặt thẻ vào giữa khung rồi chụp.';
      startBtn.textContent = 'Bật lại camera';
    } catch (err) {
      status.textContent = friendlyError(err);
      idle.style.display = 'flex';
      shotBtn.disabled = true;
    } finally {
      startBtn.disabled = false;
    }
  }

  function capture() {
    if (!stream || !video.videoWidth || !video.videoHeight) {
      status.textContent = 'Camera chưa sẵn sàng.';
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d', { alpha: false });
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    status.textContent = 'Đã chụp. Perilla Tag đang đọc màu…';
    setStateValue('image_data_url', dataUrl);
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      copyBtn.textContent = 'Đã sao chép liên kết';
    } catch (e) {
      copyBtn.textContent = 'Không sao chép được — hãy dùng menu Chia sẻ';
    }
  }

  startBtn.addEventListener('click', startCamera);
  shotBtn.addEventListener('click', capture);
  copyBtn.addEventListener('click', copyLink);

  return () => { stopCamera(); };
}
"""

camera_component = st.components.v2.component(
    name="perilla_tag_camera",
    html=CAMERA_HTML,
    css=CAMERA_CSS,
    js=CAMERA_JS,
)


def data_url_to_image(data_url: str) -> Image.Image:
    """Đổi ảnh JPEG dạng data URL từ camera thành PIL Image."""
    try:
        header, encoded = data_url.split(",", 1)
        if "base64" not in header:
            raise ValueError("Ảnh camera không đúng định dạng base64.")
        raw = base64.b64decode(encoded, validate=True)
        return normalize_image(Image.open(io.BytesIO(raw)))
    except Exception as exc:
        raise ValueError("Không đọc được ảnh từ camera.") from exc


def make_roi_preview(image: Image.Image, coords: tuple[int, int, int, int]) -> Image.Image:
    """Tạo ảnh xem trước có khung ROI; không dùng ảnh này để tính màu."""
    preview = image.copy()
    draw = ImageDraw.Draw(preview)
    x1, y1, x2, y2 = coords
    line = max(2, int(round(min(image.size) * 0.006)))
    draw.rectangle((x1, y1, x2, y2), outline=(255, 255, 255), width=line)
    return preview


def show_result_card(kind: str, title: str, message: str) -> None:
    css_class = {
        "fresh": "pt-fresh",
        "transition": "pt-transition",
        "spoiled": "pt-spoiled",
        "missing": "pt-missing",
        "error": "pt-error",
    }.get(kind, "pt-missing")
    icon = {
        "fresh": "✓",
        "transition": "!",
        "spoiled": "×",
        "missing": "◇",
        "error": "!",
    }.get(kind, "◇")
    st.markdown(
        f"""
<div class="pt-result {css_class}">
  <div class="pt-result-header">
    <div class="pt-result-icon">{icon}</div>
    <div>
      <div class="kicker">KẾT QUẢ PERILLA TAG</div>
      <div class="big">{title}</div>
    </div>
  </div>
  <p class="small">{message}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def process_and_render(image: Image.Image, source_name: str) -> None:
    """Cắt ROI, đọc màu, kiểm tra model và hiển thị kết quả."""
    try:
        image = normalize_image(image)
        roi, coords = crop_indicator_roi(image)
        color = analyze_color(roi)
    except ValueError as exc:
        show_result_card("error", "KHÔNG THỂ PHÂN TÍCH ẢNH", str(exc))
        return
    except Exception:
        show_result_card("error", "KHÔNG THỂ PHÂN TÍCH ẢNH", "Ảnh không đọc được. Hãy thử ảnh khác.")
        return

    model, model_status, model_error = load_model(MODEL_PATH)

    if model_status == "missing":
        show_result_card(
            "missing",
            "CHƯA CÓ MÔ HÌNH THỰC NGHIỆM",
            "Ảnh đã được xử lý và trích màu thành công. Mô hình phân loại sẽ được bổ sung sau khi hoàn thành dữ liệu thực nghiệm.",
        )
    elif model_status == "error":
        show_result_card(
            "error",
            "MODEL CHƯA SẴN SÀNG",
            model_error or "Không thể sử dụng model.joblib. Hãy kiểm tra lại file mô hình.",
        )
    else:
        label, prediction_error = predict_state(model, color)
        if prediction_error:
            show_result_card("error", "KHÔNG THỂ ĐỌC KẾT QUẢ MODEL", prediction_error)
        else:
            labels = {
                "fresh": (
                    "CÒN TƯƠI",
                    "Mô hình xếp màu thẻ vào nhóm CÒN TƯƠI trong điều kiện thử nghiệm của đề tài.",
                ),
                "transition": (
                    "CHUYỂN TIẾP / CẦN DÙNG SỚM",
                    "Mô hình xếp màu thẻ vào nhóm CHUYỂN TIẾP / CẦN DÙNG SỚM trong điều kiện thử nghiệm của đề tài.",
                ),
                "spoiled": (
                    "CÓ DẤU HIỆU HƯ HỎNG",
                    "Mô hình xếp màu thẻ vào nhóm CÓ DẤU HIỆU HƯ HỎNG trong điều kiện thử nghiệm của đề tài.",
                ),
            }
            title, message = labels[label]
            show_result_card(label, title, message)

    with st.expander("Xem chi tiết kỹ thuật", expanded=False):
        st.caption(f"Nguồn ảnh: {source_name}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Mean R", f"{color.r:.2f}")
        c2.metric("Mean G", f"{color.g:.2f}")
        c3.metric("Mean B", f"{color.b:.2f}")
        c4, c5, c6 = st.columns(3)
        c4.metric("Hue", f"{color.hue:.2f}°")
        c5.metric("Saturation", f"{color.saturation:.2f}%")
        c6.metric("Value", f"{color.value:.2f}%")

        st.write(f"**HEX:** `{color.hex_code}`")
        st.write(f"**Kích thước ảnh thật:** {image.width} × {image.height} px")
        st.write(f"**ROI pixel (x1, y1, x2, y2):** `{coords}`")
        st.write(
            "**ROI theo tỷ lệ:** "
            f"`x={ROI_NORMALIZED[0]:.2f}→{ROI_NORMALIZED[2]:.2f}, "
            f"y={ROI_NORMALIZED[1]:.2f}→{ROI_NORMALIZED[3]:.2f}`"
        )
        st.write(f"**Thứ tự feature cho model:** `{list(FEATURE_SCHEMA)}`")
        status_text = {
            "missing": "Chưa có model.joblib",
            "loaded": "Đã load model.joblib",
            "error": model_error or "Lỗi model.joblib",
        }[model_status]
        st.write(f"**Trạng thái model:** {status_text}")

        st.write("**Ảnh ROI thật dùng để tính màu:**")
        st.image(roi, use_container_width=False, width=min(320, max(120, roi.width)))
        st.write("**Ảnh xem trước có khung ROI:**")
        st.image(make_roi_preview(image, coords), use_container_width=True)


mode = st.radio(
    "Cách đưa ảnh vào",
    ["📷 Chụp thẻ", "▣ Chọn ảnh"],
    horizontal=True,
    label_visibility="collapsed",
)

if mode == "📷 Chụp thẻ":
    st.markdown(
        '<div class="pt-note">Mẹo: giữ điện thoại ổn định, tránh bóng đổ và đặt toàn bộ vùng màu của thẻ vào khung giữa.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    camera_result = camera_component(
        default={"image_data_url": ""},
        on_image_data_url_change=lambda: None,
        key="perilla_camera",
        width="stretch",
        height=610,
    )
    camera_data = getattr(camera_result, "image_data_url", "") or ""
    if camera_data:
        try:
            camera_image = data_url_to_image(camera_data)
            process_and_render(camera_image, "Camera")
        except ValueError as exc:
            show_result_card("error", "KHÔNG ĐỌC ĐƯỢC ẢNH CAMERA", str(exc))

else:
    if "uploader_version" not in st.session_state:
        st.session_state.uploader_version = 0

    uploaded = st.file_uploader(
        "Chọn ảnh thẻ chỉ thị",
        type=["jpg", "jpeg", "png", "webp"],
        help="Ảnh nên có thẻ nằm ở vùng giữa để ROI tự động lấy đúng màu.",
        key=f"perilla_upload_{st.session_state.uploader_version}",
    )

    if uploaded is not None:
        try:
            uploaded_image = normalize_image(Image.open(uploaded))
            st.image(uploaded_image, caption="Ảnh đã chọn", use_container_width=True)
            process_and_render(uploaded_image, "Ảnh đã chọn")
            if st.button("Phân tích ảnh khác", use_container_width=True):
                st.session_state.uploader_version += 1
                st.rerun()
        except Exception:
            show_result_card(
                "error",
                "KHÔNG ĐỌC ĐƯỢC ẢNH",
                "File ảnh không đọc được. Hãy thử JPG, JPEG, PNG hoặc WEBP khác.",
            )
    else:
        st.markdown(
            '<div class="pt-note">Chọn một ảnh có thẻ nằm gần chính giữa. Web sẽ tự lấy vùng giữa giống chế độ camera.</div>',
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# TEST GIAO DIỆN — chỉ xem màu/card, không phải kết quả phân tích
# ------------------------------------------------------------
with st.expander("Test giao diện", expanded=False):
    st.markdown(
        "**TEST GIAO DIỆN — KHÔNG PHẢI KẾT QUẢ PHÂN TÍCH**"
    )
    st.caption(
        "Các nút dưới đây chỉ dùng để xem thử màu và bố cục card. "
        "Không chạy camera, không đọc ảnh, không gọi model.joblib và không tạo dự đoán."
    )

    if "ui_test_card" not in st.session_state:
        st.session_state.ui_test_card = None

    if st.button("CÒN TƯƠI", key="ui_test_fresh", use_container_width=True):
        st.session_state.ui_test_card = "fresh"
    if st.button(
        "CHUYỂN TIẾP / CẦN DÙNG SỚM",
        key="ui_test_transition",
        use_container_width=True,
    ):
        st.session_state.ui_test_card = "transition"
    if st.button(
        "CÓ DẤU HIỆU HƯ HỎNG",
        key="ui_test_spoiled",
        use_container_width=True,
    ):
        st.session_state.ui_test_card = "spoiled"
    if st.button(
        "CHƯA CÓ MÔ HÌNH",
        key="ui_test_missing",
        use_container_width=True,
    ):
        st.session_state.ui_test_card = "missing"

    test_cards = {
        "fresh": (
            "CÒN TƯƠI",
            "Card mẫu để kiểm tra giao diện trạng thái CÒN TƯƠI.",
        ),
        "transition": (
            "CHUYỂN TIẾP / CẦN DÙNG SỚM",
            "Card mẫu để kiểm tra giao diện trạng thái CHUYỂN TIẾP / CẦN DÙNG SỚM.",
        ),
        "spoiled": (
            "CÓ DẤU HIỆU HƯ HỎNG",
            "Card mẫu để kiểm tra giao diện trạng thái CÓ DẤU HIỆU HƯ HỎNG.",
        ),
        "missing": (
            "CHƯA CÓ MÔ HÌNH THỰC NGHIỆM",
            "Card mẫu để kiểm tra giao diện khi chưa có model.joblib.",
        ),
    }

    selected_test_card = st.session_state.ui_test_card
    if selected_test_card in test_cards:
        test_title, test_message = test_cards[selected_test_card]
        show_result_card(selected_test_card, test_title, test_message)

st.markdown(
    """
<div class="pt-footer">
Kết quả mang tính hỗ trợ nhận định trong điều kiện thử nghiệm của đề tài và không thay thế kiểm nghiệm an toàn thực phẩm.
</div>
""",
    unsafe_allow_html=True,
)
