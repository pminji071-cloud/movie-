import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io

# 1. 페이지 기본 설정 및 타이틀
st.set_page_config(page_title="Easy Image Filter", page_icon="📸")
st.title("📸 나만의 웹 이미지 필터 도구")
st.caption("컴퓨터 그래픽스 - 픽셀 데이터 조작 및 필터 연산 실습")

# 2. 사이드바 - 설정 및 기능 선택
st.sidebar.header("⚙️ 필터 옵션")

# 3. 메인 - 파일 업로드 예외 처리
uploaded_file = st.file_uploader("편집할 이미지를 업로드하세요 (JPG, PNG)", type=["jpg", "jpeg", "png"])

# 예외 처리 1: 파일이 업로드되지 않았을 때
if uploaded_file is None:
    st.info("👈 이미지를 업로드하면 필터 편집 기능이 활성화됩니다.")
else:
    # 이미지 불러오기
    image = Image.open(uploaded_file)
    
    # 사이드바 컨트롤 구성
    filter_type = st.sidebar.selectbox("필터 종류 선택", ["원본", "흑백(Grayscale)", "색상 반전(Invert)"])
    brightness = st.sidebar.slider("밝기 조절", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    
    # 4. 필터 연산 적용 (함수 및 핵심 로직)
    def apply_filters(img, mode, bright_factor):
        # 4-1. 색상 필터 적용
        if mode == "흑백(Grayscale)":
            img = img.convert("L").convert("RGB") # RGB 픽셀 변환 연산
        elif mode == "색상 반전(Invert)":
            if img.mode == 'RGBA':
                r, g, b, a = img.split()
                rgb_img = Image.merge('RGB', (r, g, b))
                inverted_img = ImageOps.invert(rgb_img)
                r2, g2, b2 = inverted_img.split()
                img = Image.merge('RGBA', (r2, g2, b2, a))
            else:
                img = ImageOps.invert(img.convert('RGB'))
        
        # 4-2. 밝기 연산 적용
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(bright_factor)
        
        return img

    # 처리된 이미지 얻기
    processed_image = apply_filters(image, filter_type, brightness)
    
    # 5. 화면 레이아웃 - 원본 vs 결과 비교
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🖼️ 원본 이미지")
        st.image(image, use_container_width=True)
        
    with col2:
        st.subheader("✨ 필터 적용 이미지")
        st.image(processed_image, use_container_width=True)
        
    # 예외 처리 2 & 3: 다운로드를 위한 바이너리 버퍼 변환
    buf = io.BytesIO()
    processed_image.save(buf, format="PNG")
    byte_im = buf.getvalue()
    
    st.markdown("---")
    st.download_button(
        label="💾 필터 적용된 이미지 다운로드",
        data=byte_im,
        file_name="filtered_image.png",
        mime="image/png"
    )
