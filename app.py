from __future__ import annotations

import base64
import hashlib
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

st.set_page_config(page_title="Perilla Tag", page_icon="🍃", layout="centered", initial_sidebar_state="collapsed")

# Camera giữ ROI 30% x 30% trong perilla_core.py.
# Ảnh thư viện dùng ROI nhỏ 16% x 16% vì thường chụp xa hơn.
UPLOAD_ROI_NORMALIZED = (0.42, 0.42, 0.58, 0.58)

st.markdown(
    """
<style>
html,body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 12% -5%,rgba(135,70,158,.20),transparent 31%),radial-gradient(circle at 95% 12%,rgba(88,42,105,.16),transparent 28%),linear-gradient(180deg,#160b1c 0%,#0d0811 45%,#08050b 100%);color:#faf6fb}
[data-testid="stHeader"]{background:rgba(8,5,11,.55);backdrop-filter:blur(14px)}
#MainMenu{visibility:hidden}.block-container{max-width:780px;padding-top:.8rem;padding-bottom:2rem}
.pt-hero{position:relative;overflow:hidden;border:1px solid rgba(229,201,240,.22);border-radius:25px;padding:21px 20px 19px;margin-bottom:15px;background:radial-gradient(circle at 83% 15%,rgba(194,122,219,.15),transparent 27%),linear-gradient(145deg,rgba(47,30,57,.96),rgba(18,12,22,.98));box-shadow:0 22px 60px rgba(0,0,0,.23)}
.pt-hero:after{content:"🍃";position:absolute;right:16px;top:2px;font-size:82px;opacity:.07;transform:rotate(-16deg)}
.pt-kicker{font-size:10px;letter-spacing:.15em;font-weight:850;color:#d6b4e1;margin-bottom:5px}.pt-brand{font-size:clamp(29px,6vw,42px);line-height:1;letter-spacing:-.035em;font-weight:950}.pt-slogan{margin-top:9px;color:#eee2f2;font-size:15px;font-weight:790}.pt-sub,.pt-section-sub{color:#bbaabe;font-size:13px;line-height:1.45}.pt-sub{margin-top:3px}.pt-section-title{margin-top:13px;font-size:18px;font-weight:900}.pt-section-sub{margin-top:2px;margin-bottom:7px}
.pt-note{border:1px solid rgba(226,197,237,.10);background:rgba(39,27,46,.62);color:#c4b4c8;border-radius:14px;padding:9px 11px;font-size:12px;line-height:1.45}
div[role="radiogroup"]{display:grid!important;grid-template-columns:1fr 1fr;gap:7px;padding:5px;border:1px solid rgba(226,197,237,.10);border-radius:15px;background:rgba(29,20,35,.68)}div[role="radiogroup"] label{border-radius:11px;padding:4px 7px}
[data-testid="stFileUploader"]{border:1px solid rgba(226,197,237,.10);border-radius:17px;padding:7px;background:rgba(28,19,34,.58)}
.pt-result{border-radius:20px;border:1px solid rgba(255,255,255,.08);padding:16px 17px;margin-top:13px;box-shadow:0 17px 46px rgba(0,0,0,.18)}.pt-result-header{display:flex;align-items:center;gap:11px}.pt-result-icon{width:42px;height:42px;min-width:42px;display:grid;place-items:center;border-radius:50%;border:1px solid rgba(255,255,255,.17);background:rgba(255,255,255,.08);font-size:21px;font-weight:900}.pt-result .kicker{font-size:10px;letter-spacing:.12em;font-weight:800;opacity:.8}.pt-result .big{margin-top:2px;font-size:21px;line-height:1.1;font-weight:950}.pt-result .small{margin:10px 0 0;font-size:13px;line-height:1.48}.pt-fresh{color:#ebf8ee;background:linear-gradient(145deg,rgba(44,91,58,.82),rgba(22,53,34,.88))}.pt-transition{color:#fff4dc;background:linear-gradient(145deg,rgba(116,82,34,.84),rgba(73,51,24,.90))}.pt-spoiled{color:#ffeaec;background:linear-gradient(145deg,rgba(112,49,56,.88),rgba(68,29,35,.92))}.pt-error,.pt-missing{color:#f6edf8;background:linear-gradient(145deg,rgba(74,48,83,.84),rgba(42,27,48,.91))}
[data-testid="stExpander"]{border-radius:15px;border:1px solid rgba(226,197,237,.10);background:rgba(27,19,32,.55)}.stButton>button{min-height:41px;border-radius:13px;border:1px solid rgba(226,197,237,.16);background:linear-gradient(145deg,rgba(100,56,118,.96),rgba(71,39,85,.96));color:white;font-weight:800}.stButton>button:hover{color:white;border-color:rgba(226,197,237,.30);filter:brightness(1.05)}
.pt-footer{margin-top:21px;padding:12px 14px;border-radius:15px;border:1px solid rgba(226,197,237,.10);color:#9f91a4;background:rgba(24,17,29,.58);font-size:11px;line-height:1.5;text-align:center}
@media(max-width:640px){.block-container{padding-left:.72rem;padding-right:.72rem;padding-top:.5rem}.pt-hero{border-radius:21px;padding:17px 16px 16px}.pt-brand{font-size:31px}.pt-result{border-radius:17px}}
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

CAMERA_HTML = """
<div class="pt-camera-shell">
  <div class="pt-stage">
    <video class="pt-video" autoplay playsinline muted></video>
    <canvas class="pt-canvas" hidden></canvas>
    <div class="pt-guide" hidden>
      <span class="c tl"></span><span class="c tr"></span><span class="c bl"></span><span class="c br"></span>
      <div class="pt-guide-label">Đưa vùng màu của thẻ phủ kín khung</div>
    </div>
    <div class="pt-idle"><div class="pt-cam-icon">◉</div><div>Nhấn “Bật camera” để bắt đầu</div></div>
  </div>
  <div class="pt-cam-status">Camera chưa bật.</div>
  <div class="pt-cam-actions">
    <button class="pt-start" type="button">Bật camera</button>
    <button class="pt-shot" type="button" disabled aria-label="Chụp thẻ"><span></span></button>
  </div>
</div>
"""

CAMERA_CSS = """
html,body{margin:0!important;padding:0!important;width:100%!important;height:100%!important;overflow:hidden!important;overscroll-behavior:none!important;background:transparent!important}*{box-sizing:border-box}
.pt-camera-shell{width:100%;max-height:380px;padding:6px;overflow:hidden!important;border:1px solid rgba(226,198,239,.14);border-radius:20px;background:linear-gradient(145deg,rgba(30,20,37,.96),rgba(13,9,17,.99));color:#f7f2f9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.pt-stage{position:relative;width:100%;aspect-ratio:4/3;margin:0 auto;overflow:hidden;border-radius:16px;background:radial-gradient(circle at center,#23172b,#070508);border:1px solid rgba(255,255,255,.07)}.pt-video{width:100%;height:100%;display:block;object-fit:contain;background:#050407}.pt-idle{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;padding:20px;color:#aa99b3;text-align:center;font-size:12px}.pt-cam-icon{font-size:30px;color:#bf83d3}
.pt-guide{position:absolute;left:35%;top:35%;width:30%;height:30%;pointer-events:none;z-index:4}.pt-guide:before{content:"";position:absolute;inset:0;border:2px solid rgba(226,174,246,.94);border-radius:13px;background:rgba(183,94,218,.035);box-shadow:0 0 0 999px rgba(0,0,0,.17),0 0 18px rgba(193,112,224,.18)}.pt-guide-label{position:absolute;left:50%;bottom:-28px;transform:translateX(-50%);white-space:nowrap;padding:5px 8px;border:1px solid rgba(255,255,255,.08);border-radius:999px;background:rgba(8,5,10,.88);color:#f1e8f4;font-size:10px}.c{position:absolute;width:18px;height:18px;z-index:5;border-color:#fff;border-style:solid}.tl{left:-1px;top:-1px;border-width:3px 0 0 3px}.tr{right:-1px;top:-1px;border-width:3px 3px 0 0}.bl{left:-1px;bottom:-1px;border-width:0 0 3px 3px}.br{right:-1px;bottom:-1px;border-width:0 3px 3px 0}
.pt-cam-status{min-height:16px;margin:6px 3px 0;color:#b8a7bf;font-size:11px;line-height:1.3}.pt-cam-actions{display:flex;align-items:center;justify-content:center;gap:14px;margin-top:4px}.pt-start{border:1px solid rgba(222,190,236,.20);border-radius:12px;padding:8px 12px;background:linear-gradient(145deg,rgba(110,62,130,.94),rgba(78,43,93,.98));color:#fff;font-weight:780;cursor:pointer}.pt-shot{width:54px;height:54px;display:grid;place-items:center;padding:5px;border:3px solid rgba(255,255,255,.95);border-radius:50%;background:rgba(255,255,255,.02);cursor:pointer}.pt-shot span{width:37px;height:37px;display:block;border-radius:50%;background:#fff}.pt-shot:disabled{opacity:.28;cursor:not-allowed}.pt-guide[hidden]{display:none!important}
"""

CAMERA_JS = r"""
export default function({ parentElement, setStateValue }) {
  if (parentElement.__perillaReady) return;
  parentElement.__perillaReady = true;

  const video = parentElement.querySelector('.pt-video');
  const canvas = parentElement.querySelector('.pt-canvas');
  const stage = parentElement.querySelector('.pt-stage');
  const guide = parentElement.querySelector('.pt-guide');
  const idle = parentElement.querySelector('.pt-idle');
  const startBtn = parentElement.querySelector('.pt-start');
  const shotBtn = parentElement.querySelector('.pt-shot');
  const status = parentElement.querySelector('.pt-cam-status');
  let stream = null;

  function fitStage() {
    if (!video.videoWidth || !video.videoHeight) return;
    const ratio = video.videoWidth / video.videoHeight;
    const availableWidth = Math.max(180, parentElement.clientWidth - 12);
    const maxHeight = window.innerWidth <= 640 ? 275 : 315;
    let w = availableWidth;
    let h = w / ratio;
    if (h > maxHeight) { h = maxHeight; w = h * ratio; }
    stage.style.width = `${Math.round(w)}px`;
    stage.style.height = `${Math.round(h)}px`;
    stage.style.aspectRatio = 'auto';
  }

  async function stopCamera() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    shotBtn.disabled = true;
    guide.hidden = true;
  }

  function friendlyError(err) {
    if (!err) return 'Không mở được camera. Hãy thử lại.';
    if (err.name === 'NotAllowedError' || err.name === 'SecurityError') return 'Bạn chưa cho phép dùng camera. Hãy cấp quyền camera rồi thử lại.';
    if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') return 'Không tìm thấy camera trên thiết bị.';
    if (err.name === 'NotReadableError' || err.name === 'TrackStartError') return 'Camera có thể đang được ứng dụng khác sử dụng.';
    return 'Không mở được camera. Hãy thử lại hoặc dùng Safari/Chrome.';
  }

  async function startCamera() {
    await stopCamera();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      status.textContent = 'Trình duyệt này không hỗ trợ camera web.';
      return;
    }
    startBtn.disabled = true;
    startBtn.textContent = 'Đang mở…';
    status.textContent = 'Đang xin quyền camera…';
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280, max: 1920 }, height: { ideal: 960, max: 1920 } }
      });
      video.srcObject = stream;
      await video.play();
      fitStage();
      idle.style.display = 'none';
      guide.hidden = false;
      shotBtn.disabled = false;
      status.textContent = 'Đưa vùng màu của thẻ phủ kín khung rồi chụp.';
      startBtn.textContent = 'Bật lại camera';
    } catch (err) {
      status.textContent = friendlyError(err);
      idle.style.display = 'flex';
      guide.hidden = true;
      shotBtn.disabled = true;
    } finally {
      startBtn.disabled = false;
    }
  }

  function capture() {
    if (!stream || !video.videoWidth || !video.videoHeight) { status.textContent = 'Camera chưa sẵn sàng.'; return; }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d', { alpha: false }).drawImage(video, 0, 0, canvas.width, canvas.height);
    status.textContent = 'Đã chụp. Perilla Tag đang đọc màu…';
    setStateValue('image_data_url', canvas.toDataURL('image/jpeg', 0.92));
  }

  startBtn.addEventListener('click', startCamera);
  shotBtn.addEventListener('click', capture);
  window.addEventListener('resize', () => { if (stream) fitStage(); });
  return () => stopCamera();
}
"""

camera_component = st.components.v2.component(
    name="perilla_tag_camera",
    html=CAMERA_HTML,
    css=CAMERA_CSS,
    js=CAMERA_JS,
)


def data_url_to_image(data_url: str) -> Image.Image:
    try:
        header, encoded = data_url.split(",", 1)
        if "base64" not in header:
            raise ValueError
        return normalize_image(Image.open(io.BytesIO(base64.b64decode(encoded, validate=True))))
    except Exception as exc:
        raise ValueError("Không đọc được ảnh từ camera.") from exc


def make_roi_preview(image: Image.Image, coords: tuple[int, int, int, int]) -> Image.Image:
    preview = image.copy()
    draw = ImageDraw.Draw(preview)
    x1, y1, x2, y2 = coords
    base = min(image.size)
    outer = max(5, int(round(base * 0.010)))
    inner = max(2, int(round(base * 0.004)))
    draw.rectangle((x1, y1, x2, y2), outline=(67, 22, 84), width=outer)
    inset = max(1, outer // 2)
    if (x2 - x1) > 2 * inset and (y2 - y1) > 2 * inset:
        draw.rectangle((x1 + inset, y1 + inset, x2 - inset, y2 - inset), outline=(218, 117, 248), width=inner)
    try:
        tx, ty = x1 + outer + 4, y1 + outer + 4
        bbox = draw.textbbox((tx, ty), "ROI")
        pad = max(4, int(round(base * 0.004)))
        draw.rectangle((bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad), fill=(67, 22, 84))
        draw.text((tx, ty), "ROI", fill=(255, 255, 255))
    except Exception:
        pass
    return preview


def show_result_card(kind: str, title: str, message: str) -> None:
    css_class = {"fresh":"pt-fresh","transition":"pt-transition","spoilage_sign":"pt-spoiled","error":"pt-error"}.get(kind, "pt-missing")
    icon = {"fresh":"✓","transition":"!","spoilage_sign":"×","error":"!"}.get(kind, "◇")
    st.markdown(
        f"""
<div class="pt-result {css_class}">
  <div class="pt-result-header"><div class="pt-result-icon">{icon}</div><div><div class="kicker">KẾT QUẢ PERILLA TAG</div><div class="big">{title}</div></div></div>
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
        show_result_card("error", "KHÔNG THỂ PHÂN TÍCH ẢNH", "Ảnh không đọc được. Hãy thử ảnh khác.")
        return

    labels = {
        "fresh": ("CÒN TƯƠI", "Màu thẻ nằm trong vùng Hue quan sát ở giai đoạn đầu của dữ liệu thực nghiệm."),
        "transition": ("ĐANG THAY ĐỔI", "Hue nằm trong vùng trung gian giữa hai ngưỡng thực nghiệm. Màu vàng/cam chỉ là màu giao diện, không phải màu chuẩn của thẻ."),
        "spoilage_sign": ("CÓ DẤU HIỆU HƯ HỎNG", "Màu thẻ nằm trong vùng Hue thấp gắn với các mốc đã xuất hiện dấu hiệu cảm quan bất thường trong thực nghiệm."),
    }
    title, message = labels[state]
    show_result_card(state, title, message)

    st.caption("Kết quả được suy ra từ vùng Hue thực nghiệm của đề tài, chỉ mang tính tham khảo và không thay thế kiểm nghiệm an toàn thực phẩm.")
    if quality.low_confidence:
        st.warning("**ĐỘ TIN CẬY MÀU THẤP** — Hãy chụp lại dưới ánh sáng trắng, đều và tránh phản sáng trên bề mặt thẻ.")
    if near_boundary:
        st.info("Giá trị màu đang gần ranh giới giữa hai mức.")

    with st.expander("Xem chi tiết kỹ thuật", expanded=False):
        st.caption(f"Nguồn ảnh: {source_name}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Mean R", f"{color.r:.2f}"); c2.metric("Mean G", f"{color.g:.2f}"); c3.metric("Mean B", f"{color.b:.2f}")
        c4, c5, c6 = st.columns(3)
        c4.metric("Hue", f"{color.hue:.2f}°"); c5.metric("Saturation", f"{color.saturation:.2f}%"); c6.metric("Value", f"{color.value:.2f}%")
        st.write(f"**HEX:** `{color.hex_code}`")
        st.write(f"**Kích thước ảnh:** {image.width} × {image.height} px")
        st.write(f"**ROI pixel:** `{coords}`")
        st.write(f"**ROI tỷ lệ:** `x={roi_normalized[0]:.2f}→{roi_normalized[2]:.2f}, y={roi_normalized[1]:.2f}→{roi_normalized[3]:.2f}`")
        st.write(f"**Pixel dùng:** {color.used_pixels:,}/{color.sampled_pixels:,} ({color.valid_ratio*100:.1f}%)")
        st.write(f"**Chất lượng ảnh:** {'Độ tin cậy màu thấp — ' + quality.summary if quality.low_confidence else 'Ổn'}")
        st.write(f"**Ngưỡng Hue V1:** `≥ {FRESH_HUE_MIN:.2f}°` = Còn tươi; `≤ {SPOILAGE_HUE_MAX:.2f}°` = Có dấu hiệu hư hỏng")
        st.write(f"**Cảnh báo gần biên:** ±{BOUNDARY_WARNING_DEG:.2f}°")
        st.write(f"**Feature tương lai:** `{list(FEATURE_SCHEMA)}`")
        st.write("**ROI thật dùng để tính màu:**")
        st.image(roi, use_container_width=False, width=min(280, max(120, roi.width)))


st.markdown('<div class="pt-section-title">Quét thẻ</div>', unsafe_allow_html=True)
st.markdown('<div class="pt-section-sub">Chụp trực tiếp hoặc chọn ảnh có sẵn. Vùng màu của thẻ nên nằm ở giữa ảnh.</div>', unsafe_allow_html=True)

mode = st.radio("Cách đưa ảnh vào", ["📷 Chụp thẻ", "▣ Chọn ảnh"], horizontal=True, label_visibility="collapsed")

if mode == "📷 Chụp thẻ":
    st.markdown('<div class="pt-note">Giữ điện thoại ổn định, tránh bóng đổ và đưa vùng màu của thẻ phủ kín khung tím.</div>', unsafe_allow_html=True)

    camera_result = camera_component(
        default={"image_data_url": ""},
        on_image_data_url_change=lambda: None,
        key="perilla_camera",
        width="stretch",
        height=385,
    )

    camera_data = getattr(camera_result, "image_data_url", "") or ""
    if camera_data:
        try:
            process_and_render(data_url_to_image(camera_data), "Camera", ROI_NORMALIZED)
        except ValueError as exc:
            show_result_card("error", "KHÔNG ĐỌC ĐƯỢC ẢNH CAMERA", str(exc))

    st.caption("Nếu camera không hoạt động, hãy mở Perilla Tag trực tiếp bằng Safari hoặc Chrome.")

else:
    st.session_state.setdefault("uploader_version", 0)
    st.session_state.setdefault("upload_signature", "")
    st.session_state.setdefault("upload_analyzed", False)

    uploaded = st.file_uploader(
        "Chọn ảnh thẻ chỉ thị",
        type=["jpg", "jpeg", "png", "webp"],
        help="App dùng ROI nhỏ ở giữa ảnh để hạn chế lấy nền.",
        key=f"perilla_upload_{st.session_state.uploader_version}",
    )

    if uploaded is not None:
        try:
            uploaded_bytes = uploaded.getvalue()
            signature = hashlib.sha1(uploaded_bytes).hexdigest()
            if signature != st.session_state.upload_signature:
                st.session_state.upload_signature = signature
                st.session_state.upload_analyzed = False

            uploaded_image = normalize_image(Image.open(io.BytesIO(uploaded_bytes)))
            _, upload_coords = crop_indicator_roi(uploaded_image, UPLOAD_ROI_NORMALIZED)
            upload_preview = make_roi_preview(uploaded_image, upload_coords)

            buf = io.BytesIO()
            upload_preview.save(buf, format="JPEG", quality=88)
            preview_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

            st.markdown(
                f"""
<div style="display:flex;justify-content:center;margin:8px 0 4px;">
  <div style="width:min(320px,100%);">
    <img src="data:image/jpeg;base64,{preview_b64}" alt="ROI preview" style="width:100%;height:auto;display:block;border-radius:16px;border:1px solid rgba(226,197,237,.18);"/>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.caption("Khung tím nhỏ là vùng Perilla Tag sẽ đọc màu thật. Hãy để vùng màu của thẻ phủ kín khung trước khi phân tích.")

            if st.button("Phân tích màu", type="primary", use_container_width=True):
                st.session_state.upload_analyzed = True

            if st.session_state.upload_analyzed:
                process_and_render(uploaded_image, "Ảnh đã chọn", UPLOAD_ROI_NORMALIZED)
                if st.button("Phân tích ảnh khác", use_container_width=True):
                    st.session_state.uploader_version += 1
                    st.session_state.upload_signature = ""
                    st.session_state.upload_analyzed = False
                    st.rerun()

        except Exception:
            show_result_card("error", "KHÔNG ĐỌC ĐƯỢC ẢNH", "File ảnh không đọc được. Hãy thử JPG, JPEG, PNG hoặc WEBP khác.")
    else:
        st.markdown('<div class="pt-note">Chọn ảnh có vùng màu của thẻ nằm gần chính giữa. Hãy chắc ROI tím nằm hoàn toàn trên thẻ trước khi phân tích.</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="pt-footer">Kết quả được suy ra từ vùng Hue thực nghiệm của đề tài, chỉ mang tính tham khảo và không thay thế kiểm nghiệm an toàn thực phẩm.</div>',
    unsafe_allow_html=True,
)
