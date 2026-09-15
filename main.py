from datetime import datetime, timedelta, timezone
import pandas as pd
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide",
)


def get_korean_yesterday():
    """배포 서버의 시계와 상관없이 한국 시간(UTC+9) 기준 '어제' 날짜를 YYYYMMDD 형식으로 구합니다."""
    kst_timezone = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst_timezone)
    yesterday_kst = now_kst - timedelta(days=1)
    return yesterday_kst.strftime("%Y%m%d")


def fetch_box_office():
    """KOBIS API를 호출하여 어제의 박스오피스 데이터를 가져옵니다."""
    # Secrets 처리: Secrets 설정이 안 되어 있거나 키가 없는 경우 안내
    if "KOBIS_KEY" not in st.secrets:
        return None, "Streamlit Secrets에 'KOBIS_KEY'가 설정되지 않았습니다."

    api_key = st.secrets["KOBIS_KEY"]
    target_date = get_korean_yesterday()

    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)

        # HTTP status code 확인
        if response.status_code != 200:
            return (
                None,
                f"서버 요청에 실패했습니다. (상태 코드: {response.status_code})",
            )

        data = response.json()

        # KOBIS 특유의 오류 응답(faultInfo) 처리
        if "faultInfo" in data:
            error_message = data["faultInfo"].get(
                "message", "알 수 없는 API 오류"
            )
            return (
                None,
                f"API 오류가 발생했습니다. 인증키를 확인해주세요.\n(상세 내용: {error_message})",
            )

        # 데이터 존재 여부 확인
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        if not daily_list:
            return None, "조회된 박스오피스 데이터가 없습니다."

        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 오류가 발생했습니다: {str(e)}"
    except Exception as e:
        return None, f"데이터 처리 중 오류가 발생했습니다: {str(e)}"


# --- 메인 UI 구현 ---

st.title("🎬 어제일자 박스오피스 순위")

yesterday_str = get_korean_yesterday()
formatted_date = (
    f"{yesterday_str[:4]}년 {yesterday_str[4:6]}월 {yesterday_str[6:]}일"
)
st.caption(f"기준일: {formatted_date} (한국 시간 기준 어제)")

# 데이터 로드
raw_data, error_msg = fetch_box_office()

if error_msg:
    # 요청 실패나 오류 발생 시 안내 상자 표시
    st.error("⚠️ 데이터를 불러오지 못했습니다.")
    st.info(
        f"""
    **확인해야 할 사항:**
    - {error_msg}
    - Streamlit Cloud의 App Settings > **Secrets** 메뉴에 `KOBIS_KEY = "발급받은_키"`가 올바르게 등록되어 있는지 확인하세요.
    - KOBIS 개발자 센터에서 발급받은 키가 유효한지 확인해주세요.
    """
    )
else:
    # Pandas DataFrame으로 변환 및 정제
    df = pd.DataFrame(raw_data)

    # 요청사항 필드 매핑 및 문자열 데이터 숫자 변환
    # API 필드: rank(순위), movieNm(가게명/영화명), audiCnt(관객수), audiAcc(누적관객), scrnCnt(치킨팔린수/스크린수), showCnt(손님횟수/상영횟수)
    df["rank"] = pd.to_numeric(df["rank"])
    df["audiCnt"] = pd.to_numeric(df["audiCnt"])
    df["audiAcc"] = pd.to_numeric(df["audiAcc"])
    df["scrnCnt"] = pd.to_numeric(df["scrnCnt"])
    df["showCnt"] = pd.to_numeric(df["showCnt"])

    # 필수 데이터 확인 (가게명/영화명 비어있는 경우 체크)
    if df["movieNm"].isna().any() or (df["movieNm"].str.strip() == "").any():
        st.warning("⚠️ 일부 항목의 이름 정보가 비어 있습니다.")

    # 1. 상단 1위 영화 핵심 지표 카드 3개
    top_1 = df[df["rank"] == 1].iloc[0]

    st.subheader(f"🏆 1위: {top_1['movieNm']}")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="어제 관객수", value=f"{top_1['audiCnt']:,} 명")
    with col2:
        st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    with col3:
        st.metric(label="상영 횟수 (손님횟수)", value=f"{top_1['showCnt']:,} 회")

    st.divider()

    # 2. 전체 박스오피스 데이터 표
    st.subheader("📊 전체 박스오피스 순위표")

    # 출력용 컬럼명 변경
    display_df = df[
        ["rank", "movieNm", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
    ].copy()
    display_df.columns = [
        "순위",
        "가게명",
        "관객수",
        "누적관객",
        "치킨판린수",
        "손님횟수",
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # 3. 손님 횟수(상영 횟수) 상위 5개 막대그래프
    st.subheader("📈 손님 횟수 상위 5편")
    top5_df = (
        df.sort_values(by="showCnt", ascending=False)
        .head(5)
        .set_index("movieNm")
    )

    st.bar_chart(top5_df["showCnt"])
