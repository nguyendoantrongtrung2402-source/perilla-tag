"""Kiểm tra nhanh phần xử lý màu mà không cần mở Streamlit."""

from PIL import Image

from perilla_core import ROI_NORMALIZED, analyze_color, crop_indicator_roi


def main() -> None:
    # Ảnh kỹ thuật số #808080 phải cho Mean RGB = 128,128,128; S=0%; V≈50.196%.
    image = Image.new("RGB", (200, 200), (128, 128, 128))
    roi, coords = crop_indicator_roi(image, ROI_NORMALIZED)
    result = analyze_color(roi)

    assert coords == (70, 70, 130, 130), coords
    assert abs(result.r - 128) < 1e-9
    assert abs(result.g - 128) < 1e-9
    assert abs(result.b - 128) < 1e-9
    assert abs(result.hue - 0) < 1e-9
    assert abs(result.saturation - 0) < 1e-9
    assert abs(result.value - (128 / 255 * 100)) < 1e-9
    assert result.hex_code == "#808080"

    print("PASS — ROI, Mean RGB, HSV và HEX hoạt động đúng với ảnh #808080.")
    print(f"ROI: {coords}")
    print(
        f"RGB=({result.r:.2f}, {result.g:.2f}, {result.b:.2f}), "
        f"HSV=({result.hue:.2f}°, {result.saturation:.2f}%, {result.value:.2f}%), "
        f"HEX={result.hex_code}"
    )


if __name__ == "__main__":
    main()
