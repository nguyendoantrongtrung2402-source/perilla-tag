from __future__ import annotations

import base64
import hashlib
import io
from typing import Any

import streamlit as st
from PIL import Image

from perilla_core import (
    BOUNDARY_WARNING_DEG,
    FEATURE_SCHEMA,
    FRESH_HUE_MIN,
    ROI_NORMALIZED,
    SPOILAGE_HUE_MAX,
    analyze_color,
    assess_image_quality,
    classify_hue,
    crop_indicator_roi,
    is_near_hue_boundary,
    normalize_image,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Perilla Tag",
    page_icon="🍃",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# MAIN STYLE
# ============================================================

st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 12% -5%, rgba(135,70,158,.20), transparent 31%),
    radial-gradient(circle at 95% 12%, rgba(88,42,105,.16), transparent 28%),
    linear-gradient(180deg, #160b1c 0%, #0d0811 45%, #08050b 100%);
  color: #faf6fb;
}

[data-testid="stHeader"] {
  background: rgba(8,5,11,.55);
  backdrop-filter: blur(14px);
}

#MainMenu { visibility: hidden; }

.block-container {
  max-width: 780px;
  padding-top: .75rem;
  padding-bottom: 2rem;
}

.pt-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(229,201,240,.22);
  border-radius: 25px;
  padding: 21px 20px 19px;
  margin-bottom: 15px;
  background:
    radial-gradient(circle at 83% 15%, rgba(194,122,219,.15), transparent 27%),
    linear-gradient(145deg, rgba(47,30,57,.96), rgba(18,12,22,.98));
  box-shadow: 0 22px 60px rgba(0,0,0,.23);
}

.pt-hero::after {
  content: "🍃";
  position: absolute;
  right: 16px;
  top: 2px;
  font-size: 82px;
  opacity: .07;
  transform: rotate(-16deg);
}

.pt-kicker {
  font-size: 10px;
  letter-spacing: .15em;
  font-weight: 850;
  color: #d6b4e1;
  margin-bottom: 5px;
}

.pt-brand {
  font-size: clamp(29px, 6vw, 42px);
  line-height: 1;
  letter-spacing: -.035em;
  font-weight: 950;
}

.pt-slogan {
  margin-top: 9px;
  color: #eee2f2;
  font-size: 15px;
  font-weight: 790;
}

.pt-sub,
.pt-section-sub {
  color: #bbaabe;
  font-size: 13px;
  line-height: 1.45;
}

.pt-sub { margin-top: 3px; }

.pt-section-title {
  margin-top: 13px;
  font-size: 18px;
  font-weight: 900;
}

.pt-section-sub {
  margin-top: 2px;
  margin-bottom: 7px;
}

.pt-note {
  border: 1px solid rgba(226,197,237,.10);
  background: rgba(39,27,46,.62);
  color: #c4b4c8;
  border-radius: 14px;
  padding: 9px 11px;
  font-size: 12px;
  line-height: 1.45;
}

div[role="radiogroup"] {
  display: grid !important;
  grid-template-columns: 1fr 1fr;
  gap: 7px;
  padding: 5px;
  border: 1px solid rgba(226,197,237,.10);
  border-radius: 15px;
  background: rgba(29,20,35,.68);
}

div[role="radiogroup"] label {
  border-radius: 11px;
  padding: 4px 7px;
}

[data-testid="stFileUploader"] {
  border: 1px solid rgba(226,197,237,.10);
  border-radius: 17px;
  padding: 7px;
  background: rgba(28,19,34,.58);
}

.pt-result {
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,.08);
  padding: 16px 17px;
  margin-top: 13px;
  box-shadow: 0 17px 46px rgba(0,0,0,.18);
}

.pt-result-header {
  display: flex;
  align-items: center;
  gap: 11px;
}

.pt-result-icon {
  width: 42px;
  height: 42px;
  min-width: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,.17);
  background: rgba(255,255,255,.08);
  font-size: 21px;
  font-weight: 900;
}

.pt-result .kicker {
  font-size: 10px;
  letter-spacing: .12em;
  font-weight: 800;
  opacity: .8;
}

.pt-result .big {
  margin-top: 2px;
  font-size: 21px;
  line-height: 1.1;
  font-weight: 950;
}

.pt-result .small {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.48;
}

.pt-fresh {
  color: #ebf8ee;
  background: linear-gradient(145deg, rgba(44,91,58,.82), rgba(22,53,34,.88));
}

/* Chỉ là màu giao diện, không phải màu chuẩn thực nghiệm của thẻ. */
.pt-transition {
  color: #fff4dc;
  background: linear-gradient(145deg, rgba(116,82,34,.84), rgba(73,51,24,.90));
}

.pt-spoiled {
  color: #ffeaec;
  background: linear-gradient(145deg, rgba(112,49,56,.88), rgba(68,29,35,.92));
}

.pt-error,
.pt-missing {
  color: #f6edf8;
  background: linear-gradient(145deg, rgba(74,48,83,.84), rgba(42,27,48,.91));
}

[data-testid="stExpander"] {
  border-radius: 15px;
  border: 1px solid rgba(226,197,237,.10);
  background: rgba(27,19,32,.55);
}

.stButton > button {
  min-height: 41px;
  border-radius: 13px;
  border: 1px solid rgba(226,197,237,.16);
  background: linear-gradient(145deg, rgba(100,56,118,.96), rgba(71,39,85,.96));
  color: white;
  font-weight: 800;
}

.stButton > button:hover {
  color: white;
  border-color: rgba(226,197,237,.30);
  filter: brightness(1.05);
}

.pt-footer {
  margin-top: 21px;
  padding: 12px 14px;
  border-radius: 15px;
  border: 1px solid rgba(226,197,237,.10);
  color: #9f91a4;
  background: rgba(24,17,29,.58);
  font-size: 11px;
  line-height: 1.5;
  text-align: center;
}

@media (max-width: 640px) {
  .block-container {
    padding-left: .72rem;
    padding-right: .72rem;
    padding-top: .5rem;
  }

  .pt-hero {
    border-radius: 21px;
    padding: 17px 16px 16px;
  }

  .pt-brand { font-size: 31px; }
  .pt-result { border-radius: 17px; }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="pt-hero">
  <div class="pt-kicker">SMARTPHONE COLOR READER</div>
  <div class="pt-brand">PERILLA TAG</div>
  <div class="pt-slogan">Màu thay đổi. Tươi hay thối?</div>
  <div class="pt-sub">Chụp thẻ. Perilla Tag đọc màu.</div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# CAMERA COMPONENT
# Nút chụp nằm TRONG khung camera để không bị cắt khi iframe thấp.
# ============================================================

CAMERA_HTML = """
<div class="pt-camera-shell">
  <div class="pt-stage">
    <video class="pt-video" autoplay playsinline muted></video>
    <canvas class="pt-canvas" hidden></canvas>

    <div class="pt-guide" hidden>
      <span class="c tl"></span>
      <span class="c tr"></span>
      <span class="c bl"></span>
      <span class="c br"></span>
      <div class="pt-guide-label">Đưa vùng màu của thẻ phủ kín khung</div>
    </div>

    <div class="pt-idle">
      <div class="pt-cam-icon">◉</div>
      <div>Nhấn “Bật camera” để bắt đầu</div>
    </div>

    <div class="pt-status">Camera chưa bật.</div>

    <button class="pt-start" type="button">Bật camera</button>
    <button class="pt-restart" type="button" hidden aria-label="Bật lại camera">↻</button>
    <button class="pt-shot" type="button" hidden disabled aria-label="Chụp thẻ">
      <span></span>
    </button>
  </div>
</div>
"""

CAMERA_CSS = """
html, body {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  overflow: hidden !important;
  background: transparent !important;
}

* { box-sizing: border-box; }

.pt-camera-shell {
  width: 100%;
  padding: 4px;
  overflow: hidden !important;
  color: #f7f2f9;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/*
  Giữ camera cố định 4:3.
  Không resize khung theo camera sau khi bật -> tránh iframe đổi chiều cao,
  tránh double-scroll và tránh nút chụp bị đẩy ra ngoài.
*/
.pt-stage {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  margin: 0 auto;
  overflow: hidden;
  border: 1px solid rgba(226,198,239,.14);
  border-radius: 20px;
  background: radial-gradient(circle at center, #23172b, #070508);
  box-shadow: 0 18px 46px rgba(0,0,0,.20);
}

.pt-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  background: #050407;
}

.pt-idle {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 20px;
  color: #aa99b3;
  text-align: center;
  font-size: 12px;
  pointer-events: none;
}

.pt-cam-icon {
  font-size: 30px;
  color: #bf83d3;
}

.pt-guide {
  position: absolute;
  left: 35%;
  top: 35%;
  width: 30%;
  height: 30%;
  pointer-events: none;
  z-index: 5;
}

.pt-guide::before {
  content: "";
  position: absolute;
  inset: 0;
  border: 2px solid rgba(226,174,246,.96);
  border-radius: 13px;
  background: rgba(183,94,218,.035);
  box-shadow:
    0 0 0 999px rgba(0,0,0,.12),
    0 0 18px rgba(193,112,224,.20);
}

.pt-guide-label {
  position: absolute;
  left: 50%;
  top: -29px;
  transform: translateX(-50%);
  white-space: nowrap;
  padding: 5px 8px;
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 999px;
  background: rgba(8,5,10,.84);
  color: #f1e8f4;
  font-size: 10px;
}

.c {
  position: absolute;
  width: 18px;
  height: 18px;
  z-index: 6;
  border-color: #fff;
  border-style: solid;
}

.tl { left: -1px; top: -1px; border-width: 3px 0 0 3px; }
.tr { right: -1px; top: -1px; border-width: 3px 3px 0 0; }
.bl { left: -1px; bottom: -1px; border-width: 0 0 3px 3px; }
.br { right: -1px; bottom: -1px; border-width: 0 3px 3px 0; }

.pt-status {
  position: absolute;
  left: 9px;
  right: 48px;
  top: 9px;
  z-index: 8;
  min-height: 24px;
  padding: 6px 8px;
  border-radius: 10px;
  background: rgba(8,5,10,.60);
  color: #d7c7db;
  font-size: 10px;
  line-height: 1.25;
  backdrop-filter: blur(5px);
}

.pt-start {
  position: absolute;
  left: 50%;
  bottom: 16px;
  transform: translateX(-50%);
  z-index: 10;
  border: 1px solid rgba(222,190,236,.22);
  border-radius: 13px;
  padding: 10px 15px;
  background: linear-gradient(145deg, rgba(110,62,130,.96), rgba(78,43,93,.99));
  color: #fff;
  font-weight: 800;
  cursor: pointer;
}

.pt-restart {
  position: absolute;
  right: 9px;
  top: 9px;
  z-index: 10;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,.18);
  background: rgba(8,5,10,.62);
  color: #fff;
  font-size: 18px;
  cursor: pointer;
}

.pt-shot {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  z-index: 11;
  width: 60px;
  height: 60px;
  display: grid;
  place-items: center;
  padding: 5px;
  border: 3px solid rgba(255,255,255,.96);
  border-radius: 50%;
  background: rgba(8,5,10,.30);
  box-shadow: 0 8px 24px rgba(0,0,0,.28);
  cursor: pointer;
}

.pt-shot span {
  width: 41px;
  height: 41px;
  display: block;
  border-radius: 50%;
  background: #fff;
}

.pt-shot:disabled {
  opacity: .35;
  cursor: not-allowed;
}

.pt-guide[hidden],
.pt-shot[hidden],
.pt-restart[hidden] {
  display: none !important;
}
"""

CAMERA_JS = r"""
export default function({ parentElement, setStateValue }) {
  if (parentElement.__perillaCameraReady) return;
  parentElement.__perillaCameraReady = true;

  const video = parentElement.querySelector('.pt-video');
  const canvas = parentElement.querySelector('.pt-canvas');
  const guide = parentElement.querySelector('.pt-guide');
  const idle = parentElement.querySelector('.pt-idle');
  const startBtn = parentElement.querySelector('.pt-start');
  const restartBtn = parentElement.querySelector('.pt-restart');
  const shotBtn = parentElement.querySelector('.pt-shot');
  const status = parentElement.querySelector('.pt-status');

  let stream = null;

  async function stopCamera() {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }

    video.srcObject = null;
    shotBtn.disabled = true;
    shotBtn.hidden = true;
    restartBtn.hidden = true;
    guide.hidden = true;
  }

  function friendlyError(err) {
    if (!err) return 'Không mở được camera. Hãy thử lại.';
    if (err.name === 'NotAllowedError' || err.name === 'SecurityError') {
      return 'Bạn chưa cho phép dùng camera. Hãy cấp quyền camera rồi thử lại.';
    }
    if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
      return 'Không tìm thấy camera trên thiết bị.';
    }
    if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
      return 'Camera có thể đang được ứng dụng khác sử dụng.';
    }
    if (err.name === 'OverconstrainedError') {
      return 'Camera không hỗ trợ cấu hình yêu cầu. Hãy thử lại.';
    }
    return 'Không mở được camera. Hãy thử lại bằng Safari hoặc Chrome.';
  }

  async function startCamera() {
    await stopCamera();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      status.textContent = 'Trình duyệt này không hỗ trợ camera web.';
      startBtn.hidden = false;
      return;
    }

    startBtn.hidden = false;
    startBtn.disabled = true;
    startBtn.textContent = 'Đang mở…';
    status.textContent = 'Đang xin quyền camera…';

    try {
      const constraints = {
        audio: false,
        video: {
          facingMode: { ideal: 'environment' },
          aspectRatio: { ideal: 1.3333333333 },
          width: { ideal: 1280, max: 1920 },
          height: { ideal: 960, max: 1440 }
        }
      };

      stream = await navigator.mediaDevices.getUserMedia(constraints);

      video.setAttribute('playsinline', '');
      video.setAttribute('autoplay', '');
      video.muted = true;
      video.srcObject = stream;

      if (video.readyState < 1) {
        await new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('metadata-timeout')), 5000);
          video.onloadedmetadata = () => {
            clearTimeout(timer);
            resolve();
          };
        });
      }

      await video.play();

      idle.style.display = 'none';
      guide.hidden = false;
      shotBtn.hidden = false;
      shotBtn.disabled = false;
      restartBtn.hidden = false;
      startBtn.hidden = true;
      status.textContent = 'Đưa vùng màu của thẻ phủ kín khung tím rồi chụp.';

    } catch (err) {
      console.error('Perilla camera error:', err);
      status.textContent = friendlyError(err);
      idle.style.display = 'flex';
      guide.hidden = true;
      shotBtn.hidden = true;
      restartBtn.hidden = true;
      startBtn.hidden = false;
      startBtn.textContent = 'Thử lại';
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

    status.textContent = 'Đã chụp. Perilla Tag đang đọc màu…';
    setStateValue('image_data_url', canvas.toDataURL('image/jpeg', 0.92));
  }

  startBtn.addEventListener('click', startCamera);
  restartBtn.addEventListener('click', startCamera);
  shotBtn.addEventListener('click', capture);

  return () => {
    stopCamera();
  };
}
"""

camera_component = st.components.v2.component(
    name="perilla_tag_camera_v3",
    html=CAMERA_HTML,
    css=CAMERA_CSS,
    js=CAMERA_JS,
)


# ============================================================
# UPLOAD PAN / ZOOM CROPPER COMPONENT
# ROI đứng yên. Người dùng kéo ảnh + zoom để đưa thẻ vào ROI.
# Khi bấm Phân tích, component chỉ trả tọa độ ROI trên ẢNH GỐC.
# Python crop ảnh gốc để phân tích, không phân tích ảnh đã zoom/rescale.
# ============================================================

CROPPER_HTML = """
<div class="pt-cropper-shell">
  <div class="pt-cropper-title">Canh vùng màu của thẻ</div>
  <div class="pt-cropper-help">Kéo ảnh để di chuyển • Zoom để phóng to/thu nhỏ</div>

  <div class="pt-canvas-wrap">
    <canvas class="pt-crop-canvas" width="600" height="600"></canvas>
  </div>

  <div class="pt-crop-controls">
    <button class="pt-zoom-out" type="button" aria-label="Thu nhỏ">−</button>
    <input class="pt-zoom-slider" type="range" min="1" max="12" step="0.05" value="1" />
    <button class="pt-zoom-in" type="button" aria-label="Phóng to">+</button>
    <button class="pt-reset" type="button">Đặt lại</button>
  </div>

  <div class="pt-crop-status">Đưa vùng màu của thẻ phủ kín ô tím ở giữa.</div>

  <button class="pt-analyze" type="button">Phân tích màu</button>
</div>
"""

CROPPER_CSS = """
html, body {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
  background: transparent !important;
}

* { box-sizing: border-box; }

.pt-cropper-shell {
  width: 100%;
  height: 100%;
  overflow: hidden;
  padding: 7px 8px 8px;
  border: 1px solid rgba(226,198,239,.14);
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(30,20,37,.94), rgba(13,9,17,.98));
  color: #f7f2f9;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.pt-cropper-title {
  text-align: center;
  font-size: 13px;
  font-weight: 800;
  color: #f4eaf7;
}

.pt-cropper-help {
  margin-top: 2px;
  margin-bottom: 6px;
  text-align: center;
  font-size: 10px;
  color: #ad9bb4;
}

.pt-canvas-wrap {
  width: min(334px, 100%);
  aspect-ratio: 1 / 1;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 17px;
  border: 1px solid rgba(228,200,239,.14);
  background: #070508;
  touch-action: none;
}

.pt-crop-canvas {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
}

.pt-crop-canvas.dragging { cursor: grabbing; }

.pt-crop-controls {
  width: min(334px, 100%);
  margin: 7px auto 0;
  display: grid;
  grid-template-columns: 38px minmax(90px, 1fr) 38px auto;
  gap: 6px;
  align-items: center;
}

.pt-crop-controls button {
  height: 36px;
  border: 1px solid rgba(226,198,239,.16);
  border-radius: 11px;
  background: rgba(84,48,99,.84);
  color: #fff;
  font-weight: 800;
  cursor: pointer;
}

.pt-zoom-out,
.pt-zoom-in {
  font-size: 20px;
  line-height: 1;
}

.pt-reset {
  padding: 0 10px;
  white-space: nowrap;
  font-size: 11px;
}

.pt-zoom-slider {
  width: 100%;
  accent-color: #c680dd;
}

.pt-crop-status {
  width: min(334px, 100%);
  min-height: 17px;
  margin: 6px auto 0;
  color: #ae9db4;
  font-size: 10px;
  line-height: 1.35;
  text-align: center;
}

.pt-analyze {
  width: min(334px, 100%);
  height: 42px;
  display: block;
  margin: 7px auto 0;
  border: 1px solid rgba(231,205,240,.22);
  border-radius: 13px;
  background: linear-gradient(145deg, rgba(111,62,131,.98), rgba(74,40,89,.99));
  color: white;
  font-size: 13px;
  font-weight: 850;
  cursor: pointer;
}

.pt-analyze:disabled {
  opacity: .42;
  cursor: not-allowed;
}
"""

CROPPER_JS = r"""
export default function({ parentElement, data, setStateValue }) {
  const imageUrl = data?.image_data_url ?? '';

  if (parentElement.__perillaCropperReady) {
    return;
  }
  parentElement.__perillaCropperReady = true;

  const canvas = parentElement.querySelector('.pt-crop-canvas');
  const ctx = canvas.getContext('2d', { alpha: false });
  const zoomOutBtn = parentElement.querySelector('.pt-zoom-out');
  const zoomInBtn = parentElement.querySelector('.pt-zoom-in');
  const slider = parentElement.querySelector('.pt-zoom-slider');
  const resetBtn = parentElement.querySelector('.pt-reset');
  const analyzeBtn = parentElement.querySelector('.pt-analyze');
  const status = parentElement.querySelector('.pt-crop-status');

  const CW = canvas.width;
  const CH = canvas.height;
  const ROI_SIZE = 210;
  const ROI_LEFT = (CW - ROI_SIZE) / 2;
  const ROI_TOP = (CH - ROI_SIZE) / 2;
  const ROI_RIGHT = ROI_LEFT + ROI_SIZE;
  const ROI_BOTTOM = ROI_TOP + ROI_SIZE;

  const img = new Image();
  let baseScale = 1;
  let zoom = 1;
  let centerX = CW / 2;
  let centerY = CH / 2;
  let ready = false;

  const pointers = new Map();
  let dragging = false;
  let lastPoint = null;
  let pinchStartDistance = 0;
  let pinchStartZoom = 1;

  function clamp(value, minValue, maxValue) {
    return Math.min(maxValue, Math.max(minValue, value));
  }

  function currentScale() {
    return baseScale * zoom;
  }

  function clampCenter() {
    if (!ready) return;

    const scale = currentScale();
    const halfW = img.naturalWidth * scale / 2;
    const halfH = img.naturalHeight * scale / 2;

    const minX = ROI_RIGHT - halfW;
    const maxX = ROI_LEFT + halfW;
    const minY = ROI_BOTTOM - halfH;
    const maxY = ROI_TOP + halfH;

    centerX = minX <= maxX ? clamp(centerX, minX, maxX) : CW / 2;
    centerY = minY <= maxY ? clamp(centerY, minY, maxY) : CH / 2;
  }

  function drawOverlay() {
    ctx.fillStyle = 'rgba(0,0,0,.35)';
    ctx.fillRect(0, 0, CW, ROI_TOP);
    ctx.fillRect(0, ROI_BOTTOM, CW, CH - ROI_BOTTOM);
    ctx.fillRect(0, ROI_TOP, ROI_LEFT, ROI_SIZE);
    ctx.fillRect(ROI_RIGHT, ROI_TOP, CW - ROI_RIGHT, ROI_SIZE);

    ctx.strokeStyle = 'rgba(226,174,246,.98)';
    ctx.lineWidth = 5;
    ctx.strokeRect(ROI_LEFT, ROI_TOP, ROI_SIZE, ROI_SIZE);

    const corner = 34;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 7;
    ctx.beginPath();

    ctx.moveTo(ROI_LEFT, ROI_TOP + corner);
    ctx.lineTo(ROI_LEFT, ROI_TOP);
    ctx.lineTo(ROI_LEFT + corner, ROI_TOP);

    ctx.moveTo(ROI_RIGHT - corner, ROI_TOP);
    ctx.lineTo(ROI_RIGHT, ROI_TOP);
    ctx.lineTo(ROI_RIGHT, ROI_TOP + corner);

    ctx.moveTo(ROI_LEFT, ROI_BOTTOM - corner);
    ctx.lineTo(ROI_LEFT, ROI_BOTTOM);
    ctx.lineTo(ROI_LEFT + corner, ROI_BOTTOM);

    ctx.moveTo(ROI_RIGHT - corner, ROI_BOTTOM);
    ctx.lineTo(ROI_RIGHT, ROI_BOTTOM);
    ctx.lineTo(ROI_RIGHT, ROI_BOTTOM - corner);

    ctx.stroke();

    ctx.fillStyle = 'rgba(28,12,34,.82)';
    ctx.fillRect(ROI_LEFT, ROI_TOP - 39, 165, 31);
    ctx.fillStyle = '#f6eafa';
    ctx.font = '700 18px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif';
    ctx.fillText('VÙNG ĐỌC MÀU', ROI_LEFT + 10, ROI_TOP - 17);
  }

  function draw() {
    ctx.fillStyle = '#08060a';
    ctx.fillRect(0, 0, CW, CH);

    if (!ready) {
      ctx.fillStyle = '#baa8c0';
      ctx.font = '700 22px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Đang tải ảnh…', CW / 2, CH / 2);
      ctx.textAlign = 'start';
      return;
    }

    const scale = currentScale();
    const drawW = img.naturalWidth * scale;
    const drawH = img.naturalHeight * scale;
    const left = centerX - drawW / 2;
    const top = centerY - drawH / 2;

    ctx.drawImage(img, left, top, drawW, drawH);
    drawOverlay();
  }

  function resetTransform() {
    if (!ready) return;

    const fitScale = Math.min(CW / img.naturalWidth, CH / img.naturalHeight);
    const roiCoverScale = Math.max(ROI_SIZE / img.naturalWidth, ROI_SIZE / img.naturalHeight);

    baseScale = Math.max(fitScale, roiCoverScale);
    zoom = 1;
    centerX = CW / 2;
    centerY = CH / 2;
    slider.value = '1';
    clampCenter();
    draw();
    status.textContent = 'Kéo ảnh và zoom đến khi vùng màu của thẻ phủ kín ô tím.';
  }

  function setZoom(newZoom) {
    zoom = clamp(newZoom, 1, 12);
    slider.value = String(zoom);
    clampCenter();
    draw();
  }

  function canvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * CW / rect.width,
      y: (event.clientY - rect.top) * CH / rect.height,
    };
  }

  function distanceBetweenPointers() {
    const values = Array.from(pointers.values());
    if (values.length < 2) return 0;
    return Math.hypot(values[0].x - values[1].x, values[0].y - values[1].y);
  }

  function selectionFromTransform() {
    const scale = currentScale();
    const imageLeft = centerX - img.naturalWidth * scale / 2;
    const imageTop = centerY - img.naturalHeight * scale / 2;

    const x1 = (ROI_LEFT - imageLeft) / scale;
    const y1 = (ROI_TOP - imageTop) / scale;
    const x2 = (ROI_RIGHT - imageLeft) / scale;
    const y2 = (ROI_BOTTOM - imageTop) / scale;

    return {
      x1: clamp(x1 / img.naturalWidth, 0, 1),
      y1: clamp(y1 / img.naturalHeight, 0, 1),
      x2: clamp(x2 / img.naturalWidth, 0, 1),
      y2: clamp(y2 / img.naturalHeight, 0, 1),
      nonce: Date.now(),
    };
  }

  canvas.addEventListener('pointerdown', event => {
    if (!ready) return;
    event.preventDefault();
    canvas.setPointerCapture(event.pointerId);
    const point = canvasPoint(event);
    pointers.set(event.pointerId, point);

    if (pointers.size === 1) {
      dragging = true;
      lastPoint = point;
      canvas.classList.add('dragging');
    } else if (pointers.size === 2) {
      dragging = false;
      pinchStartDistance = distanceBetweenPointers();
      pinchStartZoom = zoom;
    }
  });

  canvas.addEventListener('pointermove', event => {
    if (!ready || !pointers.has(event.pointerId)) return;
    event.preventDefault();

    const point = canvasPoint(event);
    pointers.set(event.pointerId, point);

    if (pointers.size >= 2) {
      const distance = distanceBetweenPointers();
      if (pinchStartDistance > 0) {
        setZoom(pinchStartZoom * distance / pinchStartDistance);
      }
      return;
    }

    if (dragging && lastPoint) {
      centerX += point.x - lastPoint.x;
      centerY += point.y - lastPoint.y;
      lastPoint = point;
      clampCenter();
      draw();
    }
  });

  function releasePointer(event) {
    pointers.delete(event.pointerId);

    if (pointers.size === 0) {
      dragging = false;
      lastPoint = null;
      canvas.classList.remove('dragging');
    } else if (pointers.size === 1) {
      dragging = true;
      lastPoint = Array.from(pointers.values())[0];
      pinchStartDistance = 0;
    }
  }

  canvas.addEventListener('pointerup', releasePointer);
  canvas.addEventListener('pointercancel', releasePointer);

  canvas.addEventListener('wheel', event => {
    if (!ready) return;
    event.preventDefault();
    const factor = event.deltaY < 0 ? 1.10 : 1 / 1.10;
    setZoom(zoom * factor);
  }, { passive: false });

  zoomOutBtn.addEventListener('click', () => setZoom(zoom / 1.20));
  zoomInBtn.addEventListener('click', () => setZoom(zoom * 1.20));
  slider.addEventListener('input', () => setZoom(Number(slider.value)));
  resetBtn.addEventListener('click', resetTransform);

  analyzeBtn.addEventListener('click', () => {
    if (!ready) return;
    const selection = selectionFromTransform();
    status.textContent = 'Đã chọn vùng. Perilla Tag đang phân tích màu…';
    setStateValue('selection', selection);
  });

  img.onload = () => {
    ready = true;
    analyzeBtn.disabled = false;
    resetTransform();
  };

  img.onerror = () => {
    ready = false;
    analyzeBtn.disabled = true;
    status.textContent = 'Không tải được ảnh xem trước.';
    draw();
  };

  analyzeBtn.disabled = true;
  img.src = imageUrl;
  draw();
}
"""

cropper_component = st.components.v2.component(
    name="perilla_tag_upload_cropper_v1",
    html=CROPPER_HTML,
    css=CROPPER_CSS,
    js=CROPPER_JS,
)


# ============================================================
# IMAGE HELPERS
# ============================================================


def data_url_to_image(data_url: str) -> Image.Image:
    try:
        header, encoded = data_url.split(",", 1)
        if "base64" not in header:
            raise ValueError
        raw = base64.b64decode(encoded, validate=True)
        return normalize_image(Image.open(io.BytesIO(raw)))
    except Exception as exc:
        raise ValueError("Không đọc được ảnh từ camera.") from exc


def image_to_component_data_url(image: Image.Image, max_side: int = 1600) -> str:
    """
    Tạo ảnh preview nhẹ cho component pan/zoom.
    Chỉ dùng để CANH ROI trên màn hình.
    Dữ liệu màu vẫn crop từ image gốc ở Python.
    """
    preview = normalize_image(image).copy()
    preview.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    preview.save(buffer, format="JPEG", quality=90, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def selection_to_roi(selection: Any) -> tuple[float, float, float, float]:
    """Đọc tọa độ normalized do cropper JS trả về và kiểm tra an toàn."""
    if selection is None:
        raise ValueError("Chưa chọn vùng màu.")

    if isinstance(selection, dict):
        getter = selection.get
    else:
        getter = lambda key, default=None: getattr(selection, key, default)

    try:
        x1 = float(getter("x1"))
        y1 = float(getter("y1"))
        x2 = float(getter("x2"))
        y2 = float(getter("y2"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Tọa độ vùng màu không hợp lệ.") from exc

    values = (x1, y1, x2, y2)
    if not all(0.0 <= value <= 1.0 for value in values):
        raise ValueError("Vùng màu nằm ngoài ảnh.")
    if not (x1 < x2 and y1 < y2):
        raise ValueError("Kích thước vùng màu không hợp lệ.")
    if (x2 - x1) < 0.01 or (y2 - y1) < 0.01:
        raise ValueError("Vùng màu quá nhỏ để phân tích.")

    return values


# ============================================================
# RESULT UI
# ============================================================


def show_result_card(kind: str, title: str, message: str) -> None:
    css_class = {
        "fresh": "pt-fresh",
        "transition": "pt-transition",
        "spoilage_sign": "pt-spoiled",
        "error": "pt-error",
    }.get(kind, "pt-missing")

    icon = {
        "fresh": "✓",
        "transition": "!",
        "spoilage_sign": "×",
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


def process_and_render(
    image: Image.Image,
    source_name: str,
    roi_normalized: tuple[float, float, float, float],
) -> None:
    try:
        image = normalize_image(image)
        roi, coords = crop_indicator_roi(image, roi_normalized)
        color = analyze_color(roi)
        state = classify_hue(color.hue)
        quality = assess_image_quality(color)
        near_boundary = is_near_hue_boundary(color.hue)
    except ValueError as exc:
        show_result_card("error", "KHÔNG THỂ PHÂN TÍCH ẢNH", str(exc))
        return
    except Exception:
        show_result_card(
            "error",
            "KHÔNG THỂ PHÂN TÍCH ẢNH",
            "Ảnh không đọc được. Hãy thử ảnh khác.",
        )
        return

    labels = {
        "fresh": (
            "CÒN TƯƠI",
            "Màu thẻ nằm trong vùng Hue quan sát ở giai đoạn đầu của dữ liệu thực nghiệm.",
        ),
        "transition": (
            "ĐANG THAY ĐỔI",
            "Hue nằm trong vùng trung gian giữa hai ngưỡng thực nghiệm. Màu vàng/cam chỉ là màu giao diện, không phải màu chuẩn của thẻ.",
        ),
        "spoilage_sign": (
            "CÓ DẤU HIỆU HƯ HỎNG",
            "Màu thẻ nằm trong vùng Hue thấp gắn với các mốc đã xuất hiện dấu hiệu cảm quan bất thường trong thực nghiệm.",
        ),
    }

    title, message = labels[state]
    show_result_card(state, title, message)

    st.caption(
        "Kết quả được suy ra từ vùng Hue thực nghiệm của đề tài, "
        "chỉ mang tính tham khảo và không thay thế kiểm nghiệm an toàn thực phẩm."
    )

    if quality.low_confidence:
        st.warning(
            "**ĐỘ TIN CẬY MÀU THẤP** — Hãy chụp lại dưới ánh sáng trắng, "
            "đều và tránh phản sáng trên bề mặt thẻ."
        )

    if near_boundary:
        st.info("Giá trị màu đang gần ranh giới giữa hai mức.")

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
        st.write(f"**Kích thước ảnh:** {image.width} × {image.height} px")
        st.write(f"**ROI pixel:** `{coords}`")
        st.write(
            "**ROI tỷ lệ:** "
            f"`x={roi_normalized[0]:.4f}→{roi_normalized[2]:.4f}, "
            f"y={roi_normalized[1]:.4f}→{roi_normalized[3]:.4f}`"
        )
        st.write(
            f"**Pixel dùng:** {color.used_pixels:,}/{color.sampled_pixels:,} "
            f"({color.valid_ratio * 100:.1f}%)"
        )
        st.write(
            "**Chất lượng ảnh:** "
            + (
                "Độ tin cậy màu thấp — " + quality.summary
                if quality.low_confidence
                else "Ổn"
            )
        )
        st.write(
            f"**Ngưỡng Hue V1:** `≥ {FRESH_HUE_MIN:.2f}°` = Còn tươi; "
            f"`≤ {SPOILAGE_HUE_MAX:.2f}°` = Có dấu hiệu hư hỏng"
        )
        st.write(f"**Cảnh báo gần biên:** ±{BOUNDARY_WARNING_DEG:.2f}°")
        st.write(f"**Feature tương lai:** `{list(FEATURE_SCHEMA)}`")
        st.write("**ROI thật dùng để tính màu:**")
        st.image(
            roi,
            use_container_width=False,
            width=min(280, max(120, roi.width)),
        )


# ============================================================
# APP FLOW
# ============================================================

st.markdown('<div class="pt-section-title">Quét thẻ</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="pt-section-sub">Chụp trực tiếp hoặc chọn ảnh có sẵn.</div>',
    unsafe_allow_html=True,
)

mode = st.radio(
    "Cách đưa ảnh vào",
    ["📷 Chụp thẻ", "▣ Chọn ảnh"],
    horizontal=True,
    label_visibility="collapsed",
)


# ----------------------------
# CAMERA
# ----------------------------

if mode == "📷 Chụp thẻ":
    st.markdown(
        '<div class="pt-note">Giữ điện thoại ổn định, tránh bóng đổ và đưa vùng màu của thẻ phủ kín khung tím. Nút chụp nằm ngay trong camera để không bị cắt khỏi màn hình.</div>',
        unsafe_allow_html=True,
    )

    camera_result = camera_component(
        default={"image_data_url": ""},
        on_image_data_url_change=lambda: None,
        key="perilla_camera_v3",
        width="stretch",
        height=350,
    )

    camera_data = getattr(camera_result, "image_data_url", "") or ""

    if camera_data:
        try:
            camera_image = data_url_to_image(camera_data)
            process_and_render(camera_image, "Camera", ROI_NORMALIZED)
        except ValueError as exc:
            show_result_card("error", "KHÔNG ĐỌC ĐƯỢC ẢNH CAMERA", str(exc))

    st.caption(
        "Nếu camera không hoạt động, hãy mở Perilla Tag trực tiếp bằng Safari hoặc Chrome."
    )


# ----------------------------
# UPLOAD + PAN / ZOOM
# ----------------------------

else:
    st.markdown(
        '<div class="pt-note">Sau khi chọn ảnh, kéo ảnh sang trái/phải/lên/xuống và zoom để đưa đúng vùng màu của thẻ vào ô tím. Zoom chỉ dùng để canh; màu được tính từ pixel ảnh gốc.</div>',
        unsafe_allow_html=True,
    )

    st.session_state.setdefault("uploader_version", 0)

    uploaded = st.file_uploader(
        "Chọn ảnh thẻ chỉ thị",
        type=["jpg", "jpeg", "png", "webp"],
        help="Sau khi chọn ảnh, bạn có thể kéo và zoom để canh vùng thẻ trước khi phân tích.",
        key=f"perilla_upload_{st.session_state.uploader_version}",
    )

    if uploaded is not None:
        try:
            uploaded_bytes = uploaded.getvalue()
            signature = hashlib.sha1(uploaded_bytes).hexdigest()
            uploaded_image = normalize_image(Image.open(io.BytesIO(uploaded_bytes)))
            component_image_url = image_to_component_data_url(uploaded_image)

            crop_result = cropper_component(
                data={"image_data_url": component_image_url},
                default={"selection": None},
                on_selection_change=lambda: None,
                key=f"perilla_cropper_{signature[:16]}",
                width="stretch",
                height=530,
            )

            selection = getattr(crop_result, "selection", None)

            if selection:
                try:
                    upload_roi = selection_to_roi(selection)
                    process_and_render(uploaded_image, "Ảnh đã chọn", upload_roi)
                except ValueError as exc:
                    show_result_card("error", "KHÔNG THỂ DÙNG VÙNG ĐÃ CHỌN", str(exc))

                if st.button("Chọn ảnh khác", use_container_width=True):
                    st.session_state.uploader_version += 1
                    st.rerun()

        except Exception:
            show_result_card(
                "error",
                "KHÔNG ĐỌC ĐƯỢC ẢNH",
                "File ảnh không đọc được. Hãy thử JPG, JPEG, PNG hoặc WEBP khác.",
            )
    else:
        st.caption(
            "Thẻ có thể nằm ở bất kỳ vị trí nào trong ảnh. Sau khi tải ảnh lên, bạn sẽ tự kéo và zoom để canh ROI."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="pt-footer">Kết quả được suy ra từ vùng Hue thực nghiệm của đề tài, chỉ mang tính tham khảo và không thay thế kiểm nghiệm an toàn thực phẩm.</div>',
    unsafe_allow_html=True,
)
