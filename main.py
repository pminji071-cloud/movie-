import pandas as pd
import streamlit as st

# Streamlit 페이지 기본 설정 (페이지 제목 및 넓은 레이아웃 적용)
st.set_page_config(page_title="인기 반려견 품종 순위", layout="wide")

# 반려견 품종 데이터 정의 (KB 경영연구소 한국 반려동물 보고서 참조)
# 실제 데이터가 없을 때를 대비해 가독성 높은 구조로 기본 데이터를 작성합니다.
DOG_BREEDS_DATA = [
    {
        "rank": 1,
        "breed": "몰티즈 (Maltese)",
        "share": 23.7,
        "size": "소형견",
        "feature": "털 빠짐이 적고 성격이 온순하여 한국 실내 주거 환경에 매우 적합함",
    },
    {
        "rank": 2,
        "breed": "푸들 (Poodle)",
        "share": 19.0,
        "size": "소형/중형견",
        "feature": "지능이 매우 높고 털 빠짐이 거의 없어 초보 양육자에게 인기 만점",
    },
    {
        "rank": 3,
        "breed": "믹스견/하이브리드견 (말티푸 등)",
        "share": 14.2,
        "size": "변동",
        "feature": "유전적 질환 위험이 적고 개성 있는 외모 (특히 말티푸의 인기가 높음)",
    },
    {
        "rank": 4,
        "breed": "포메라니안 (Pomeranian)",
        "share": 11.0,
        "size": "소형견",
        "feature": "풍성한 털과 인형 같은 외모, 호기심이 많고 애교가 넘침",
    },
    {
        "rank": 5,
        "breed": "진돗개 (Jindo Dog)",
        "share": 5.8,
        "size": "중/대형견",
        "feature": "한국 토종견으로 주인에 대한 충성심과 깔끔한 위생 관리가 강점",
    },
    {
        "rank": 6,
        "breed": "시츄 (Shih Tzu)",
        "share": 4.6,
        "size": "소형견",
        "feature": "헛짖음이 적고 조용하며 온순하여 바쁜 가구에 적합",
    },
    {
        "rank": 7,
        "breed": "비숑 프리제 (Bichon Frise)",
        "share": 4.5,
        "size": "소형견",
        "feature": "솜사탕 같은 곱슬 털과 명랑하고 사교성이 좋은 성격",
    },
]


def load_data():
    """데이터를 로드하여 데이터프레임으로 변환하는 함수입니다."""
    try:
        df = pd.DataFrame(DOG_BREEDS_DATA)
        if df.empty:
            st.warning(
                "⚠️ 표시할 데이터가 없습니다. 데이터 설정을 확인해 주세요."
            )
            return None
        return df
    except Exception as e:
        st.error(
            "❌ 데이터를 불러오는 도중 에러가 발생했습니다. 코드 설정을 확인해 주세요."
        )
        st.caption(f"상세 오류: {e}")
        return None


# ----------------------------------------------------
# 메인 화면 표시 로직 시작
# ----------------------------------------------------

st.title("🐶 한국에서 가장 많이 키우는 강아지 품종 순위")
st.text("출처: 한국 반려동물 양육 현황 보고서 (KB 경영연구소)")

# 데이터 불러오기
df = load_data()

if df is not None:
    # 1. 1위 강아지 품종 지표 카드 3장으로 크게 표시
    top_breed = df.iloc[0]
    st.subheader("🥇 한국인에게 가장 사랑받는 강아지 1위")

    # 화면을 3개의 칼럼으로 나누기
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="품종명", value=top_breed["breed"])
    with col2:
        st.metric(label="양육 비중", value=f"{top_breed['share']}%")
    with col3:
        st.metric(label="체구 구분", value=top_breed["size"])

    st.caption(f"💡 주요 특징: {top_breed['feature']}")

    st.divider()

    # 2. 양육 비중 상위 5개 품종 막대그래프
    st.subheader("📊 인기 강아지 품종 Top 5 (양육 비중 %)")
    top_5_df = df.head(5)

    # 그래프 생성을 위해 품종명을 인덱스로 설정
    chart_data = top_5_df[["breed", "share"]].set_index("breed")
    st.bar_chart(chart_data)

    st.divider()

    # 3. 전체 순위 표 출력
    st.subheader("📋 전체 인기 반려견 품종 순위")

    # 표로 표시할 컬럼 정리 및 한국어 헤더 변경
    display_df = df[["rank", "breed", "share", "size", "feature"]].copy()
    display_df.columns = ["순위", "품종명", "양육 비중 (%)", "크기 구분", "주요 특징"]

    # 표 출력 (왼쪽 기본 인덱스 번호 숨김 처리)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
