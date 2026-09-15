import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="어제의 영화 박스오피스", layout="wide")

st.title("🎬 어제의 영화 박스오피스")
st.caption("KOBIS(영화관입장권통합전산망) API 데이터를 기반으로 제공됩니다.")

# 1. secrets에서 KOBIS API 키 불러오기
try:
    api_key = st.secrets["KOBIS_KEY"]
except Exception:
    st.error(
        "🔒 **API 키를 찾을 수 없습니다.**\n\n"
        "Streamlit Cloud의 App Settings > Secrets 항목에 `KOBIS_KEY = '발급받은키'` 형식으로 설정했는지 확인해 주세요."
    )
    st.stop()

# 2. 한국 시간(KST) 기준 '어제' 날짜 계산 (서버 시간대가 달라 발생하는 오류 방지)
kst_timezone = pytz.timezone("Asia/Seoul")
today_kst = datetime.datetime.now(kst_timezone)
yesterday_kst = today_kst - datetime.timedelta(days=1)
target_date = yesterday_kst.strftime("%Y%m%d")

st.info(f"📅 조회 기준 날짜 (KST 어제): **{yesterday_kst.strftime('%Y년 %m월 %d일')}**")

# 3. KOBIS API 요청
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {"key": api_key, "targetDt": target_date}

try:
    response = requests.get(url, params=params, timeout=10)

    # HTTP 네트워크 요청 실패 처리
    if response.status_code != 200:
        st.error(
            f"⚠️ **서버 통신 실패 (상태 코드: {response.status_code})**\n\n"
            "KOBIS API 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."
        )
        st.stop()

    data = response.json()

    # API 응답 내 faultInfo(인증키 오류 등) 예외 처리
    if "faultInfo" in data:
        error_msg = data["faultInfo"].get("message", "알 수 없는 오류가 발생했습니다.")
        st.error(
            f"⚠️ **API 인증 오류가 발생했습니다.**\n\n"
            f"**오류 메시지:** {error_msg}\n\n"
            "등록된 `KOBIS_KEY`가 올바른지 KOBIS 오픈API 마이페이지에서 확인해 주세요."
        )
        st.stop()

    # 박스오피스 목록 추출
    box_office_list = (
        data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
    )

    # 데이터가 비어있거나 영화명이 제공되지 않는 경우 처리
    if not box_office_list or not box_office_list[0].get("movieNm"):
        st.warning(
            "⚠️ **박스오피스 데이터를 불러올 수 없거나 데이터가 비어 있습니다.**\n\n"
            "KOBIS API 집계 지연이 발생했거나 대상 날짜의 데이터가 존재하지 않을 수 있습니다."
        )
        st.stop()

    # 4. 데이터프레임(Dataframe) 생성 및 숫자형 변환
    df = pd.DataFrame(box_office_list)

    # 문자열로 들어오는 수치형 데이터를 정수형(int)으로 변환
    numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 5. 1위 영화 지표 카드 (Metrics)
    top_1 = df.iloc[0]
    st.subheader("🏆 어제의 1위 영화")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="영화명", value=top_1["movieNm"])
    with col2:
        st.metric(label="일일 관객수", value=f"{top_1['audiCnt']:,} 명")
    with col3:
        st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")

    st.markdown("---")

    # 6. 관객수 상위 5편 막대그래프
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5).copy()

    # Streamlit 막대그래프용 데이터 정렬 및 시각화
    chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
    chart_data.columns = ["일일 관객수"]
    st.bar_chart(chart_data)

    st.markdown("---")

    # 7. 전체 박스오피스 순위 표 (Table)
    st.subheader("📋 전체 순위표")

    # 사용자에게 보여줄 컬럼 선택 및 이름 변경
    display_df = df[["rank", "movieNm", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    display_df.columns = ["순위", "영화명", "관객수", "누적관객", "스크린수"]

    # 천 단위 쉼표 서식 적용
    formatted_df = display_df.copy()
    formatted_df["관객수"] = formatted_df["관객수"].apply(lambda x: f"{x:,}")
    formatted_df["누적관객"] = formatted_df["누적관객"].apply(lambda x: f"{x:,}")
    formatted_df["스크린수"] = formatted_df["스크린수"].apply(lambda x: f"{x:,}")

    st.dataframe(formatted_df, use_container_width=True, hide_index=True)

except requests.exceptions.RequestException as e:
    st.error(
        f"🌐 **네트워크 오류가 발생했습니다.**\n\n"
        f"세부 정보: {e}\n\n"
        "인터넷 연결 상태를 확인하거나 잠시 후 다시 시도해 주세요."
    )
