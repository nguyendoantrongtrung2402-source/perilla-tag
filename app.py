from __future__ import annotations

import base64
import io

import streamlit as st
from PIL import Image, ImageDraw

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
# CẤU HÌNH TRANG
# ============================================================

st.set_page_config(
    page_title="Perilla Tag",
    page_icon="🍃",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# GIAO DIỆN CHÍNH
# ============================================================

st.markdown(
    """
<style>
:root {
  --pt-bg-0: #08050b;
  --pt-bg-1: #120b17;
  --pt-card: rgba(31, 21, 38, 0.84);
  --pt-border: rgba(229, 201, 240, 0.14);
  --pt-border-strong: rgba(229, 201, 240, 0.24);
  --pt-text: #faf6fb;
  --pt-muted: #bbaabe;
  --pt-purple: #c684de;
}

html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 12% -5%, rgba(135, 70, 158, .20), transparent 31%),
    radial-gradient(circle at 95% 12%, rgba(88, 42, 105, .16), transparent 28%),
    linear-gradient(180deg, #160b1c 0%, #0d0811 45%, #08050b 100%);
  color: var(--pt-text);
}

[data-testid="stHeader"] {
  background: rgba(8, 5, 11, .55);
  backdrop-filter: blur(14px);
}

#MainMenu { visibility: hidden; }

.block-container {
  max-width: 780px;
  padding-top: .9rem;
  padding-bottom: 2.2rem;
}

.pt-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--pt-border-strong);
  border-radius: 27px;
  padding: 23px 22px 21px;
  margin-bottom: 16px;
  background:
    radial-gradient(circle at 83% 15%, rgba(194, 122, 219, .15), transparent 27%),
    linear-gradient(145deg, rgba(47, 30, 57, .96), rgba(18, 12, 22, .98));
  box-shadow: 0 23px 65px rgba(0,0,0,.24);
}

.pt-hero::after {
  content: "🍃";
  position: absolute;
  right: 16px;
  top: 3px;
  font-size: 86px;
  opacity: .07;
  transform: rotate(-16deg);
  pointer-events: none;
}

.pt-kicker {
  font-size: 11px;
  letter-spacing: .15em;
  font-weight: 850;
  color: #d6b4e1;
  margin-bottom: 5px;
}

.pt-brand {
  margin: 0;
  font-size: clamp(29px, 6vw, 43px);
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

.pt-sub {
  margin-top: 3px;
  color: var(--pt-muted);
  font-size: 13px;
}

.pt-section-title {
  margin-top: 13px;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: -.02em;
}

.pt-section-sub {
  margin-top: 2px;
  margin-bottom: 7px;
  color: var(--pt-muted);
  font-size: 13px;
  line-height: 1.45;
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

/* Tabs chọn camera / upload */
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

/* Result */
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
  opacity: .92;
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
    padding-top: .55rem;
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
# ============================================================

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

    <div class="pt-guide" aria-hidden="true" hidden>
      <span class="c tl"></span>
      <span class="c tr"></span>
      <span class="c bl"></span>
      <span class="c br"></span>
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
    <button
      class="pt-shot"
      type="button"
      disabled
      aria-label="Chụp thẻ"
      title="Chụp thẻ"
    >
      <span></span>
    </button>
  </div>

  <button class="pt-copy" type="button" hidden>
    Sao chép liên kết
  </button>
</div>
"""

CAMERA_CSS = """
html, body {
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  background: transparent !important;
}

* {
  box-sizing: border-box;
}

.pt-camera-shell {
  width: 100%;
  padding: 8px;
  overflow: hidden;
  border: 1px solid rgba(226,198,239,.14);
  border-radius: 20px;
  background:
    linear-gradient(
      145deg,
      rgba(30,20,37,.96),
      rgba(13,9,17,.99)
    );
  color: #f7f2f9;
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
}

.pt-cam-topline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 7px 2px;
  color: #cbb8d2;
  font-size: 12px;
  font-weight: 750;
}

.pt-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #bf75d9;
  box-shadow: 0 0 13px rgba(191,117,217,.68);
}

.pt-stage {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 17px;
  background:
    radial-gradient(
      circle at center,
      #23172b,
      #070508
    );
  border: 1px solid rgba(255,255,255,.07);
}

.pt-video {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
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
  color: #aa99b3;
  text-align: center;
  font-size: 12px;
}

.pt-cam-icon {
  font-size: 30px;
  color: #bf83d3;
}

/* ROI chỉ hiện sau khi camera thật đã mở. */
.pt-guide {
  position: absolute;
  left: 35%;
  top: 35%;
  width: 30%;
  height: 30%;
  pointer-events: none;
  z-index: 4;
}

.pt-guide::before {
  content: "";
  position: absolute;
  inset: 0;
  border: 2px solid rgba(226,174,246,.94);
  border-radius: 13px;
  background: rgba(183,94,218,.035);
  box-shadow:
    0 0 0 999px rgba(0,0,0,.17),
    0 0 18px rgba(193,112,224,.18);
}

.pt-guide-label {
  position: absolute;
  left: 50%;
  bottom: -28px;
  transform: translateX(-50%);
  white-space: nowrap;
  padding: 5px 8px;
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 999px;
  background: rgba(8,5,10,.88);
  color: #f1e8f4;
  font-size: 10px;
}

.c {
  position: absolute;
  width: 18px;
  height: 18px;
  z-index: 5;
  border-color: #fff;
  border-style: solid;
}

.tl {
  left: -1px;
  top: -1px;
  border-width: 3px 0 0 3px;
  border-radius: 8px 0 0 0;
}

.tr {
  right: -1px;
  top: -1px;
  border-width: 3px 3px 0 0;
  border-radius: 0 8px 0 0;
}

.bl {
  left: -1px;
  bottom: -1px;
  border-width: 0 0 3px 3px;
  border-radius: 0 0 0 8px;
}

.br {
  right: -1px;
  bottom: -1px;
  border-width: 0 3px 3px 0;
  border-radius: 0 0 8px 0;
}

.pt-cam-status {
  min-height: 17px;
  margin: 7px 3px 1px;
  color: #b8a7bf;
  font-size: 11px;
  line-height: 1.35;
}

.pt-cam-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 5px;
}

.pt-start,
.pt-copy {
  border: 1px solid rgba(222,190,236,.20);
  border-radius: 12px;
  padding: 8px 12px;
  background:
    linear-gradient(
      145deg,
      rgba(110,62,130,.94),
      rgba(78,43,93,.98)
    );
  color: #fff;
  font-weight: 780;
  cursor: pointer;
}

.pt-shot {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  padding: 5px;
  border: 3px solid rgba(255,255,255,.95);
  border-radius: 50%;
  background: rgba(255,255,255,.02);
  cursor: pointer;
}

.pt-shot span {
  width: 40px;
  height: 40px;
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

.pt-browser-warning {
  margin: 0 0 8px;
  padding: 9px 10px;
  border: 1px solid rgba(235,172,89,.24);
  border-radius: 12px;
  background: rgba(119,72,31,.28);
  color: #f2d8b7;
  font-size: 11px;
  line-height: 1.4;
}

.pt-copy {
  margin: 6px auto 0;
  font-size: 11px;
}

/* hidden phải thật sự ẩn */
.pt-copy[hidden],
.pt-browser-warning[hidden],
.pt-guide[hidden] {
  display: none !important;
}
"""

CAMERA_JS = r"""
export default function({ parentElement, setStateValue }) {
  if (parentElement.__perillaReady) return;
  parentElement.__perillaReady = true;

  const video =
    parentElement.querySelector('.pt-video');

  const canvas =
    parentElement.querySelector('.pt-canvas');

  const stage =
    parentElement.querySelector('.pt-stage');

  const guide =
    parentElement.querySelector('.pt-guide');

  const idle =
    parentElement.querySelector('.pt-idle');

  const startBtn =
    parentElement.querySelector('.pt-start');

  const shotBtn =
    parentElement.querySelector('.pt-shot');

  const status =
    parentElement.querySelector('.pt-cam-status');

  const warning =
    parentElement.querySelector('.pt-browser-warning');

  const copyBtn =
    parentElement.querySelector('.pt-copy');

  let stream = null;

  const ua =
    navigator.userAgent || '';

  const inApp =
    /FBAN|FBAV|Instagram|Line\/|Zalo|Messenger/i
      .test(ua);

  if (inApp) {
    warning.hidden = false;
    warning.textContent =
      'Bạn đang mở trong trình duyệt nhúng. '
      + 'Nếu camera không chạy, hãy mở '
      + 'Perilla Tag bằng Chrome hoặc Safari.';

    copyBtn.hidden = false;
  }

  if (
    !window.isSecureContext
    &&
    location.hostname !== 'localhost'
  ) {
    warning.hidden = false;

    warning.textContent =
      'Camera web cần kết nối HTTPS. '
      + 'Hãy dùng bản đã deploy hoặc mở trên localhost.';
  }

  function fitStageToVideo() {
    if (
      !video.videoWidth
      ||
      !video.videoHeight
    ) {
      return;
    }

    const ratio =
      video.videoWidth
      /
      video.videoHeight;

    const availableWidth =
      Math.max(
        180,
        parentElement.clientWidth - 16
      );

    /*
    Giới hạn chiều cao để component
    không sinh thanh cuộn thứ hai.
    */
    const maxHeight =
      window.innerWidth <= 640
        ? 320
        : 360;

    let stageWidth =
      availableWidth;

    let stageHeight =
      stageWidth / ratio;

    if (
      stageHeight > maxHeight
    ) {
      stageHeight =
        maxHeight;

      stageWidth =
        stageHeight * ratio;
    }

    stage.style.width =
      `${Math.round(stageWidth)}px`;

    stage.style.height =
      `${Math.round(stageHeight)}px`;

    stage.style.aspectRatio =
      'auto';

    stage.style.margin =
      '0 auto';
  }

  async function stopCamera() {
    if (stream) {
      stream
        .getTracks()
        .forEach(
          track => track.stop()
        );

      stream = null;
    }

    shotBtn.disabled = true;
    guide.hidden = true;
  }

  function friendlyError(err) {
    if (!err) {
      return (
        'Không mở được camera. '
        + 'Hãy thử lại.'
      );
    }

    if (
      err.name === 'NotAllowedError'
      ||
      err.name === 'SecurityError'
    ) {
      return (
        'Bạn chưa cho phép dùng camera. '
        + 'Hãy cấp quyền camera rồi thử lại.'
      );
    }

    if (
      err.name === 'NotFoundError'
      ||
      err.name === 'DevicesNotFoundError'
    ) {
      return (
        'Không tìm thấy camera trên thiết bị.'
      );
    }

    if (
      err.name === 'NotReadableError'
      ||
      err.name === 'TrackStartError'
    ) {
      return (
        'Camera có thể đang được ứng dụng khác sử dụng. '
        + 'Hãy đóng ứng dụng đó rồi thử lại.'
      );
    }

    if (
      err.name === 'OverconstrainedError'
    ) {
      return (
        'Camera không hỗ trợ cấu hình yêu cầu. '
        + 'Hãy thử lại.'
      );
    }

    return (
      'Không mở được camera. '
      + 'Hãy thử bằng Chrome/Safari '
      + 'và kiểm tra quyền camera.'
    );
  }

  async function startCamera() {
    await stopCamera();

    if (
      !navigator.mediaDevices
      ||
      !navigator.mediaDevices.getUserMedia
    ) {
      status.textContent =
        'Trình duyệt này không hỗ trợ camera web. '
        + 'Hãy dùng Chrome hoặc Safari.';

      return;
    }

    startBtn.disabled = true;
    startBtn.textContent = 'Đang mở…';
    status.textContent = 'Đang xin quyền camera…';

    try {
      stream =
        await navigator
          .mediaDevices
          .getUserMedia(
            {
              audio: false,

              video: {
                facingMode: {
                  ideal: 'environment'
                },

                width: {
                  ideal: 1280,
                  max: 1920
                },

                height: {
                  ideal: 960,
                  max: 1920
                }
              }
            }
          );

      video.srcObject = stream;

      await video.play();

      /*
      Chỉ lúc camera thật đã mở
      mới biết tỉ lệ ảnh chính xác.
      */
      fitStageToVideo();

      idle.style.display = 'none';

      /*
      ROI chỉ hiện lúc này.
      */
      guide.hidden = false;

      shotBtn.disabled = false;

      status.textContent =
        'Camera đã sẵn sàng. '
        + 'Đặt vùng màu của thẻ vào khung rồi chụp.';

      startBtn.textContent =
        'Bật lại camera';

    } catch (err) {
      status.textContent =
        friendlyError(err);

      idle.style.display =
        'flex';

      guide.hidden =
        true;

      shotBtn.disabled =
        true;
    }

    finally {
      startBtn.disabled =
        false;
    }
  }

  function capture() {
    if (
      !stream
      ||
      !video.videoWidth
      ||
      !video.videoHeight
    ) {
      status.textContent =
        'Camera chưa sẵn sàng.';

      return;
    }

    canvas.width =
      video.videoWidth;

    canvas.height =
      video.videoHeight;

    const ctx =
      canvas.getContext(
        '2d',
        {
          alpha: false
        }
      );

    ctx.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    const dataUrl =
      canvas.toDataURL(
        'image/jpeg',
        0.92
      );

    status.textContent =
      'Đã chụp. '
      + 'Perilla Tag đang đọc màu…';

    setStateValue(
      'image_data_url',
      dataUrl
    );
  }

  async function copyLink() {
    try {
      await navigator
        .clipboard
        .writeText(
          window.location.href
        );

      copyBtn.textContent =
        'Đã sao chép liên kết';

    } catch (e) {
      copyBtn.textContent =
        'Không sao chép được — hãy dùng menu Chia sẻ';
    }
  }

  startBtn.addEventListener(
    'click',
    startCamera
  );

  shotBtn.addEventListener(
    'click',
    capture
  );

  copyBtn.addEventListener(
    'click',
    copyLink
  );

  window.addEventListener(
    'resize',
    () => {
      if (stream) {
        fitStageToVideo();
      }
    }
  );

  return () => {
    stopCamera();
  };
}
"""

camera_component = st.components.v2.component(
    name="perilla_tag_camera",
    html=CAMERA_HTML,
    css=CAMERA_CSS,
    js=CAMERA_JS,
)


# ============================================================
# HÀM XỬ LÝ ẢNH / HIỂN THỊ
# ============================================================

def data_url_to_image(
    data_url: str,
) -> Image.Image:
    """Đổi ảnh JPEG data URL từ camera thành PIL Image."""

    try:
        header, encoded = data_url.split(
            ",",
            1,
        )

        if "base64" not in header:
            raise ValueError(
                "Ảnh camera không đúng định dạng base64."
            )

        raw = base64.b64decode(
            encoded,
            validate=True,
        )

        return normalize_image(
            Image.open(
                io.BytesIO(raw)
            )
        )

    except Exception as exc:
        raise ValueError(
            "Không đọc được ảnh từ camera."
        ) from exc


def make_roi_preview(
    image: Image.Image,
    coords: tuple[int, int, int, int],
) -> Image.Image:
    """
    Tạo preview có ROI tím rõ để người dùng biết app sẽ đọc vùng nào.
    Preview này KHÔNG dùng để tính màu.
    """

    preview = image.copy()

    draw = ImageDraw.Draw(
        preview
    )

    x1, y1, x2, y2 = coords

    base = min(
        image.size
    )

    outer_width = max(
        5,
        int(
            round(
                base * 0.010
            )
        ),
    )

    inner_width = max(
        2,
        int(
            round(
                base * 0.004
            )
        ),
    )

    # Viền tím đậm ngoài.
    draw.rectangle(
        (
            x1,
            y1,
            x2,
            y2,
        ),
        outline=(
            67,
            22,
            84,
        ),
        width=outer_width,
    )

    inset = max(
        1,
        outer_width // 2
    )

    if (
        (x2 - x1) > 2 * inset
        and
        (y2 - y1) > 2 * inset
    ):
        draw.rectangle(
            (
                x1 + inset,
                y1 + inset,
                x2 - inset,
                y2 - inset,
            ),
            outline=(
                218,
                117,
                248,
            ),
            width=inner_width,
        )

    label = "ROI"

    text_x = (
        x1 + outer_width + 4
    )

    text_y = (
        y1 + outer_width + 4
    )

    try:
        bbox = draw.textbbox(
            (
                text_x,
                text_y,
            ),
            label,
        )

        pad = max(
            4,
            int(
                round(
                    base * 0.004
                )
            ),
        )

        draw.rectangle(
            (
                bbox[0] - pad,
                bbox[1] - pad,
                bbox[2] + pad,
                bbox[3] + pad,
            ),
            fill=(
                67,
                22,
                84,
            ),
        )

        draw.text(
            (
                text_x,
                text_y,
            ),
            label,
            fill=(
                255,
                255,
                255,
            ),
        )

    except Exception:
        pass

    return preview


def show_result_card(
    kind: str,
    title: str,
    message: str,
) -> None:

    css_class = {
        "fresh":
            "pt-fresh",

        "transition":
            "pt-transition",

        "spoilage_sign":
            "pt-spoiled",

        "spoiled":
            "pt-spoiled",

        "error":
            "pt-error",

        "missing":
            "pt-missing",
    }.get(
        kind,
        "pt-missing",
    )

    icon = {
        "fresh":
            "✓",

        "transition":
            "!",

        "spoilage_sign":
            "×",

        "spoiled":
            "×",

        "error":
            "!",

        "missing":
            "◇",
    }.get(
        kind,
        "◇",
    )

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

  <p class="small">
    {message}
  </p>
</div>
""",
        unsafe_allow_html=True,
    )


def process_and_render(
    image: Image.Image,
    source_name: str,
) -> None:
    """
    Ảnh
    → ROI
    → màu
    → Hue
    → phân loại V1
    → hiển thị.
    """

    try:
        image = normalize_image(
            image
        )

        roi, coords = crop_indicator_roi(
            image
        )

        color = analyze_color(
            roi
        )

        state = classify_hue(
            color.hue
        )

        quality = assess_image_quality(
            color
        )

        near_boundary = is_near_hue_boundary(
            color.hue
        )

    except ValueError as exc:
        show_result_card(
            "error",
            "KHÔNG THỂ PHÂN TÍCH ẢNH",
            str(exc),
        )
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
            (
                "Màu thẻ nằm trong vùng Hue "
                "quan sát ở giai đoạn đầu "
                "của dữ liệu thực nghiệm."
            ),
        ),

        "transition": (
            "ĐANG THAY ĐỔI",
            (
                "Hue nằm trong vùng trung gian "
                "giữa hai ngưỡng thực nghiệm. "
                "Màu vàng/cam của card chỉ dùng "
                "để phân biệt giao diện, không phải "
                "màu chuẩn của thẻ."
            ),
        ),

        "spoilage_sign": (
            "CÓ DẤU HIỆU HƯ HỎNG",
            (
                "Màu thẻ nằm trong vùng Hue thấp "
                "gắn với các mốc đã xuất hiện "
                "dấu hiệu cảm quan bất thường "
                "trong thực nghiệm."
            ),
        ),
    }

    title, message = labels[
        state
    ]

    show_result_card(
        state,
        title,
        message,
    )

    st.caption(
        "Kết quả được suy ra từ vùng Hue thực nghiệm "
        "của đề tài, chỉ mang tính tham khảo và không "
        "thay thế kiểm nghiệm an toàn thực phẩm."
    )

    if quality.low_confidence:
        st.warning(
            "**ĐỘ TIN CẬY MÀU THẤP** — "
            "Ảnh có thể bị ảnh hưởng bởi ánh sáng, "
            "phản chiếu hoặc vùng màu quá ít bão hòa. "
            "Hãy chụp lại dưới ánh sáng trắng, đều "
            "và tránh phản sáng trên bề mặt thẻ."
        )

    if near_boundary:
        st.info(
            "Giá trị màu đang gần ranh giới giữa hai mức. "
            "Trạng thái chính vẫn được xác định theo "
            "ngưỡng Hue V1 đã chốt."
        )

    with st.expander(
        "Xem chi tiết kỹ thuật",
        expanded=False,
    ):
        st.caption(
            f"Nguồn ảnh: {source_name}"
        )

        c1, c2, c3 = st.columns(
            3
        )

        c1.metric(
            "Mean R",
            f"{color.r:.2f}",
        )

        c2.metric(
            "Mean G",
            f"{color.g:.2f}",
        )

        c3.metric(
            "Mean B",
            f"{color.b:.2f}",
        )

        c4, c5, c6 = st.columns(
            3
        )

        c4.metric(
            "Hue",
            f"{color.hue:.2f}°",
        )

        c5.metric(
            "Saturation",
            f"{color.saturation:.2f}%",
        )

        c6.metric(
            "Value",
            f"{color.value:.2f}%",
        )

        st.write(
            f"**HEX:** `{color.hex_code}`"
        )

        st.write(
            "**Kích thước ảnh thật:** "
            f"{image.width} × "
            f"{image.height} px"
        )

        st.write(
            "**ROI pixel "
            "(x1, y1, x2, y2):** "
            f"`{coords}`"
        )

        st.write(
            "**ROI theo tỷ lệ:** "
            f"`x={ROI_NORMALIZED[0]:.2f}"
            f"→{ROI_NORMALIZED[2]:.2f}, "
            f"y={ROI_NORMALIZED[1]:.2f}"
            f"→{ROI_NORMALIZED[3]:.2f}`"
        )

        st.write(
            "**Pixel dùng để tính màu:** "
            f"{color.used_pixels:,}/"
            f"{color.sampled_pixels:,} "
            f"({color.valid_ratio * 100:.1f}%)"
        )

        st.write(
            "**Pixel bị loại ở bước sáng/tối:** "
            f"{color.extreme_reject_ratio * 100:.1f}%"
        )

        st.write(
            "**Bộ lọc dự phòng:** "
            + (
                "Có — ROI có quá ít pixel "
                "qua bước lọc ban đầu"
                if color.filter_fallback
                else "Không"
            )
        )

        st.write(
            "**Chất lượng ảnh:** "
            + (
                f"Độ tin cậy màu thấp — {quality.summary}"
                if quality.low_confidence
                else "Ổn"
            )
        )

        st.write(
            "**Ngưỡng Hue V1:** "
            f"`≥ {FRESH_HUE_MIN:.2f}°` = Còn tươi; "
            f"`≤ {SPOILAGE_HUE_MAX:.2f}°` "
            "= Có dấu hiệu hư hỏng"
        )

        st.write(
            "**Vùng cảnh báo gần ranh giới:** "
            f"±{BOUNDARY_WARNING_DEG:.2f}° "
            "(tham số kỹ thuật giao diện, "
            "không phải ngưỡng khoa học)"
        )

        st.write(
            "**Thứ tự feature nếu phát triển model sau này:** "
            f"`{list(FEATURE_SCHEMA)}`"
        )

        st.write(
            "**Ảnh ROI thật dùng để tính màu:**"
        )

        st.image(
            roi,
            use_container_width=False,
            width=min(
                320,
                max(
                    120,
                    roi.width,
                ),
            ),
        )

        st.write(
            "**Ảnh xem trước có khung ROI:**"
        )

        st.image(
            make_roi_preview(
                image,
                coords,
            ),
            use_container_width=True,
        )


# ============================================================
# LUỒNG ỨNG DỤNG
# ============================================================

st.markdown(
    '<div class="pt-section-title">Quét thẻ</div>',
    unsafe_allow_html=True,
)

st.markdown(
    (
        '<div class="pt-section-sub">'
        'Chụp trực tiếp hoặc chọn ảnh có sẵn. '
        'Vùng màu của thẻ nên nằm ở giữa ảnh.'
        '</div>'
    ),
    unsafe_allow_html=True,
)

mode = st.radio(
    "Cách đưa ảnh vào",
    [
        "📷 Chụp thẻ",
        "▣ Chọn ảnh",
    ],
    horizontal=True,
    label_visibility="collapsed",
)


# ============================================================
# CAMERA
# ============================================================

if mode == "📷 Chụp thẻ":

    st.markdown(
        (
            '<div class="pt-note">'
            'Mẹo: giữ điện thoại ổn định, tránh bóng đổ. '
            'Khung ROI chỉ xuất hiện sau khi camera thật '
            'đã mở để khớp đúng hướng ảnh.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.write("")

    camera_result = camera_component(
        default={
            "image_data_url": ""
        },
        on_image_data_url_change=lambda: None,
        key="perilla_camera",
        width="stretch",
        height=500,
    )

    camera_data = (
        getattr(
            camera_result,
            "image_data_url",
            "",
        )
        or ""
    )

    if camera_data:
        try:
            camera_image = data_url_to_image(
                camera_data
            )

            process_and_render(
                camera_image,
                "Camera",
            )

        except ValueError as exc:
            show_result_card(
                "error",
                "KHÔNG ĐỌC ĐƯỢC ẢNH CAMERA",
                str(exc),
            )


# ============================================================
# UPLOAD
# ============================================================

else:

    if (
        "uploader_version"
        not in st.session_state
    ):
        st.session_state.uploader_version = 0

    uploaded = st.file_uploader(
        "Chọn ảnh thẻ chỉ thị",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        help=(
            "Thẻ nên nằm ở vùng giữa ảnh "
            "để ROI tự động lấy đúng màu."
        ),
        key=(
            f"perilla_upload_"
            f"{st.session_state.uploader_version}"
        ),
    )

    if uploaded is not None:

        try:

            uploaded_image = normalize_image(
                Image.open(
                    uploaded
                )
            )

            # Preview ROI để người dùng biết app đang đọc chỗ nào.
            _, upload_coords = crop_indicator_roi(
                uploaded_image
            )

            upload_preview = make_roi_preview(
                uploaded_image,
                upload_coords,
            )

            st.image(
                upload_preview,
                caption=(
                    "Khung tím là vùng "
                    "Perilla Tag sẽ đọc màu"
                ),
                use_container_width=True,
            )

            st.caption(
                "Nếu phần màu của thẻ chưa nằm trong khung tím, "
                "hãy chọn ảnh khác. Perilla Tag không tự kéo ROI "
                "ở phiên bản V1."
            )

            process_and_render(
                uploaded_image,
                "Ảnh đã chọn",
            )

            if st.button(
                "Phân tích ảnh khác",
                use_container_width=True,
            ):
                st.session_state.uploader_version += 1
                st.rerun()

        except Exception:

            show_result_card(
                "error",
                "KHÔNG ĐỌC ĐƯỢC ẢNH",
                (
                    "File ảnh không đọc được. "
                    "Hãy thử JPG, JPEG, PNG "
                    "hoặc WEBP khác."
                ),
            )

    else:

        st.markdown(
            (
                '<div class="pt-note">'
                'Chọn ảnh có thẻ nằm gần chính giữa. '
                'Sau khi tải lên, app sẽ hiện khung tím '
                'để bạn kiểm tra chính xác vùng ROI.'
                '</div>'
            ),
            unsafe_allow_html=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="pt-footer">
Kết quả được suy ra từ vùng Hue thực nghiệm của đề tài,
chỉ mang tính tham khảo và không thay thế kiểm nghiệm
an toàn thực phẩm.
</div>
""",
    unsafe_allow_html=True,
)
