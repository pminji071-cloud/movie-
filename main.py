import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 스트림릿 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="어제 박스오피스", page_icon="🎬", layout="wide"
)

st.title("🎬 어제의 박스오피스 TOP 10")


# -----------------------------------------------------------------------------
# 2. 한국 시간(KST) 기준 '어제' 날짜 계산 함수
# -----------------------------------------------------------------------------
def get_yesterday_kst():
    # 배포 서버의 시계가 해외 기준이어도 한국 시간(Asia/Seoul)으로 정확히 계산합니다.
    kst_now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    yesterday = kst_now - datetime.timedelta(days=1)
    # KOBIS API 요구 형식인 YYYYMMDD 형태로 변환합니다.
    return yesterday.strftime("%Y%m%d")


target_date = get_yesterday_kst()
st.caption(
    f"기준 날짜: {target_date[:4]}년 {target_date[4:6]}월 {target_date[6:]}일 (한국 시간 기준 어제)"
)

# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 가져오기
# -----------------------------------------------------------------------------
# Secrets에서 API 키를 불러옵니다. 키가 설정되어 있지 않으면 경고를 표시합니다.
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "🚨 Secrets 설정이 필요합니다!\n\n"
        "Streamlit Cloud의 App settings -> Secrets 메뉴에서 아래와 같이 인증키를 등록해 주세요:\n"
        '```toml\nKOBIS_KEY = "발급받은_키_문자열"\n```'
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date}

try:
    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    # KOBIS API는 인증 실패 등의 에러 발생 시 faultInfo 객체를 반환합니다.
    if "faultInfo" in data:
        st.error("🚨 API 요청 오류가 발생했습니다. 다음 사항을 확인해 주세요:")
        st.write(
            f"- **오류 메시지:** {data['faultInfo'].get('message', '알 수 없는 오류')}"
        )
        st.write(
            "- **해결 방법:** Secrets에 등록된 `KOBIS_KEY`가 올바른지, KOBIS 개발자센터에서 키가 활성화 상태인지 확인해 주세요."
        )
        st.stop()

    # 정상 응답 구조 안에서 영화 목록 데이터 추출
    box_office_result = data.get("boxOfficeResult", {})
    daily_list = box_office_result.get("dailyBoxOfficeList", [])

    # 영화 목록이 비어 있는 경우 예외 처리
    if not daily_list:
        st.warning("⚠️ 영화 목록 데이터를 불러올 수 없습니다.")
        st.info(
            "• 아직 오늘의 집계 전이거나, API 서버 측 데이터 업데이트 중일 수 있습니다.\n"
            "• 서비스 관리자 설정 및 KOBIS 제공 상태를 확인해 보세요."
        )
        st.stop()

except requests.exceptions.RequestException as e:
    st.error("🚨 네트워크 연결 문제로 API 호출에 실패했습니다.")
    st.write(f"상세 에러 내용: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 4. 데이터 전처리 (문자열 → 숫자 변환)
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

# KOBIS API에서 문자열로 넘어오는 숫자를 계산/시각화용 정수형(int)으로 변환합니다.
numeric_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# -----------------------------------------------------------------------------
# 5. UI 화면 구성 (지표 카드 + 차트 + 표)
# -----------------------------------------------------------------------------

# [1위 영화 주요 지표 카드]
top_1 = df.iloc[0]
st.subheader(f"🥇 1위: {top_1['movieNm']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="어제 관객수", value=f"{top_1['audiCnt']:,} 명")
with col2:
    st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
with col3:
    st.metric(label="상영 스크린수", value=f"{top_1['scrnCnt']:,} 개")

st.divider()

# [상위 5개 영화 막대그래프]
st.subheader("📊 관객수 상위 5개 영화")
top_5_df = df.head(5)

# 관객수 기준 막대그래프 생성
st.bar_chart(data=top_5_df, x="movieNm", y="audiCnt", color="#FF4B4B")

st.divider()

# [전체 10위 표 구성]
st.subheader("📋 박스오피스 전체 순위")

# 요청사항에 맞는 컬럼 선택 및 보기 좋은 이름으로 변경
display_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수",
]

# 표 형태로 출력 (천 단위 쉼표 포맷팅)
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "관객수": st.column_config.NumberColumn(format="%d명"),
        "누적관객": st.column_config.NumberColumn(format="%d명"),
        "스크린수": st.column_config.NumberColumn(format="%d개"),
    },
)
