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

st.set_page_config(
    page_title="Perilla Tag",
    page_icon="🍃",
    layout="centered",
    initial_sidebar_state="collapsed",
)


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


[data-testid="stMain"], .stMain, .block-container { position: relative; z-index: 1; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: .45rem; }
#MainMenu { visibility: hidden; }

.block-container {
  max-width: 980px;
  padding-top: 1rem;
  padding-bottom: 2.8rem;
}

/* HERO gọn, không dùng asset ảnh; ưu tiên mobile */
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


/* RESULT CARDS */
.pt-result {
  margin: 1rem 0 1.15rem;
  padding: 1.15rem 1.2rem 1.05rem;
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 22px;
  color: #fff;
  box-shadow: 0 18px 44px rgba(0,0,0,.20);
  animation: ptFadeUp .22s ease-out;
}

.pt-result-header {
  display: flex;
  align-items: center;
  gap: .9rem;
}

.pt-result-icon {
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255,255,255,.13);
  border: 1px solid rgba(255,255,255,.15);
  font-size: 1.45rem;
  font-weight: 900;
}

.pt-result .kicker {
  margin-bottom: .18rem;
  color: rgba(255,255,255,.72);
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .09em;
}

.pt-result .big {
  color: #fff;
  font-size: 1.34rem;
  font-weight: 900;
  line-height: 1.15;
}

.pt-result .small {
  margin: .85rem 0 0;
  color: rgba(255,255,255,.86);
  font-size: .92rem;
  line-height: 1.5;
}

.pt-fresh {
  background: radial-gradient(circle at 90% 8%, rgba(83,224,143,.20), transparent 32%),
              linear-gradient(145deg, #18563a 0%, #0f3827 100%);
  border-color: rgba(109,228,157,.34);
  box-shadow: 0 18px 44px rgba(9,55,32,.28), 0 0 34px rgba(75,207,128,.11);
}

.pt-transition {
  background: radial-gradient(circle at 90% 8%, rgba(255,193,79,.22), transparent 32%),
              linear-gradient(145deg, #80551d 0%, #52350f 100%);
  border-color: rgba(255,205,110,.34);
  box-shadow: 0 18px 44px rgba(72,48,12,.28), 0 0 34px rgba(244,173,55,.11);
}

.pt-spoiled {
  background: radial-gradient(circle at 90% 8%, rgba(255,105,117,.22), transparent 32%),
              linear-gradient(145deg, #7a2731 0%, #4c1720 100%);
  border-color: rgba(255,139,149,.33);
  box-shadow: 0 18px 44px rgba(75,22,29,.28), 0 0 34px rgba(239,91,103,.11);
}

.pt-missing {
  background: radial-gradient(circle at 90% 8%, rgba(210,132,237,.20), transparent 32%),
              linear-gradient(145deg, #583967 0%, #35243f 100%);
  border-color: rgba(222,173,240,.29);
  box-shadow: 0 18px 44px rgba(47,30,57,.26), 0 0 34px rgba(184,108,211,.10);
}

.pt-error {
  background: radial-gradient(circle at 90% 8%, rgba(255,105,117,.20), transparent 32%),
              linear-gradient(145deg, #682535 0%, #411722 100%);
  border-color: rgba(244,128,139,.30);
}

@keyframes ptFadeUp {
  from { opacity: 0; transform: translateY(7px); }
  to   { opacity: 1; transform: translateY(0); }
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
  /* Mobile-first: mở app là tới thao tác chụp/chọn ảnh gần như ngay lập tức. */
  .block-container {
    padding-left: .68rem;
    padding-right: .68rem;
    padding-top: .35rem;
    padding-bottom: 1.7rem;
  }

  .pt-hero {
    min-height: 0;
    margin-bottom: .58rem;
    padding: 13px 14px 12px;
    border-radius: 18px;
    box-shadow: 0 14px 34px rgba(0,0,0,.22);
  }
  .pt-hero::before,
  .pt-hero::after { display: none; }

  .pt-hero-copy { width: 82%; max-width: none; }
  .pt-eyebrow {
    margin-bottom: .28rem;
    font-size: .56rem;
    letter-spacing: .22em;
  }
  .pt-title {
    margin-bottom: .30rem;
    font-size: clamp(1.48rem, 7.2vw, 1.95rem);
    line-height: .98;
    letter-spacing: -.035em;
  }
  .pt-slogan {
    margin-bottom: 0;
    font-size: .80rem;
    line-height: 1.25;
  }
  .pt-sub { display: none; }
  .pt-hero-copy { width: 100%; }

  /* Hero đã đủ hướng dẫn trên điện thoại; bỏ block giới thiệu thứ hai để giảm cuộn. */
  .pt-section { display: none; }

  div[role="radiogroup"] {
    width: 100%;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: .42rem;
    margin-top: 0;
    margin-bottom: .18rem;
  }
  div[role="radiogroup"] label {
    width: 100% !important;
    min-width: 0 !important;
    min-height: 44px;
    padding: .50rem .42rem;
    border-radius: 13px;
    font-size: .83rem;
    white-space: nowrap;
    overflow: hidden;
    box-sizing: border-box;
  }
  div[role="radiogroup"] label > div:first-child {
    flex: 0 0 auto;
  }
  div[role="radiogroup"] label p {
    white-space: nowrap !important;
    margin: 0 !important;
  }

  .pt-note {
    margin: .35rem 0 .42rem;
    font-size: .75rem;
    line-height: 1.36;
  }

  [data-testid="stFileUploader"] { border-radius: 14px; }
  [data-testid="stFileUploaderDropzone"] {
    padding-top: .55rem;
    padding-bottom: .55rem;
    min-height: 72px;
  }

  [data-testid="stExpander"] { border-radius: 14px; }
  [data-testid="stMetric"] {
    border-radius: 12px;
    padding: .34rem .45rem;
  }

  .pt-result {
    margin: .58rem 0 .72rem;
    padding: .85rem .88rem .82rem;
    border-radius: 17px;
  }
  .pt-result-header { gap: .65rem; }
  .pt-result-icon {
    width: 37px;
    height: 37px;
    flex-basis: 37px;
    border-radius: 11px;
    font-size: 1.18rem;
  }
  .pt-result .kicker { font-size: .61rem; }
  .pt-result .big { font-size: 1.05rem; }
  .pt-result .small {
    margin-top: .58rem;
    font-size: .80rem;
    line-height: 1.42;
  }

  .pt-footer {
    margin-top: 1.05rem;
    padding-top: .65rem;
    font-size: .68rem;
  }

  [data-testid="stAppViewContainer"]::before { display: none; }
  [data-testid="stAppViewContainer"]::after { opacity: .025; }
}

@media (max-width: 390px) {
  .block-container { padding-left: .52rem; padding-right: .52rem; }
  .pt-hero { padding: 11px 12px 10px; border-radius: 16px; }
  .pt-title { font-size: 1.40rem; }
  .pt-slogan { font-size: .74rem; }
  div[role="radiogroup"] label { font-size: .74rem; padding-left: .22rem; padding-right: .22rem; }
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
</div>

<div class="pt-section">
  <div class="pt-section-title">Quét thẻ</div>
  <p class="pt-section-sub">Chụp trực tiếp hoặc chọn ảnh có sẵn. Đặt vùng màu của thẻ vào chính giữa để Perilla Tag tự lấy ROI.</p>
</div>
"""

st.html(UI_HTML)

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
  aspect-ratio: 4 / 3;
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
  .pt-cam-topline { display: none; }
  .pt-stage {
    border-radius: 18px;
    aspect-ratio: 4 / 3 !important;
    max-height: none;
  }
  .pt-guide::before { border-radius: 11px; }
  .pt-guide-label {
    bottom: -27px;
    padding: 4px 7px;
    font-size: 10px;
  }
  .pt-cam-status {
    min-height: 16px;
    margin: 7px 2px 1px;
    font-size: 10.5px;
  }
  .pt-cam-actions {
    gap: 15px;
    margin-top: 4px;
  }
  .pt-start,
  .pt-copy {
    min-height: 40px;
    padding: 8px 12px;
    border-radius: 11px;
    font-size: 12px;
  }
  .pt-shot {
    width: 62px;
    height: 62px;
    padding: 4px;
  }
  .pt-shot span {
    width: 44px;
    height: 44px;
  }
  .pt-browser-warning {
    margin-bottom: 7px;
    padding: 8px 9px;
    border-radius: 11px;
    font-size: 10.5px;
  }
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
          aspectRatio: { ideal: 1.3333333333 },
          width: { ideal: 1280, max: 1920 },
          height: { ideal: 960, max: 1440 }
        }
      };
      stream = await navigator.mediaDevices.getUserMedia(constraints);
      video.srcObject = stream;
      await video.play();
      // Giữ khung camera cố định 4:3 để giao diện không phình cao sau khi bật camera.
      // Camera ưu tiên tỉ lệ 4:3; video dùng object-fit: cover để không đổi chiều cao UI.
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
    camera_result = camera_component(
        default={"image_data_url": ""},
        on_image_data_url_change=lambda: None,
        key="perilla_camera",
        width="stretch",
        height="content",
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
            # Không hiện ảnh lớn trước kết quả trên mobile; ảnh + ROI vẫn có trong "Xem chi tiết kỹ thuật".
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

st.markdown(
    """
<div class="pt-footer">
Kết quả mang tính hỗ trợ nhận định trong điều kiện thử nghiệm của đề tài và không thay thế kiểm nghiệm an toàn thực phẩm.
</div>
""",
    unsafe_allow_html=True,
)
