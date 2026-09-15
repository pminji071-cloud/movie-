import datetime
import pandas as pd
import requests
import streamlit as st

# Streamlit 페이지 기본 설정 (제목 및 레이아웃)
st.set_page_config(page_title="어제의 영화 박스오피스", layout="wide")


def get_yesterday_kst():
    """한국 시간(KST, UTC+9) 기준으로 어제 날짜를 YYYYMMDD 형식으로 반환합니다."""
    # 서버 시계 설정과 상관없이 UTC 기준 시간에 9시간을 더해 한국 시간을 구합니다.
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    kst_now = now_utc + datetime.timedelta(hours=9)
    yesterday_kst = kst_now - datetime.timedelta(days=1)
    return yesterday_kst.strftime("%Y%m%d")


def fetch_box_office_data(api_key, target_date):
    """KOBIS API를 호출하여 데이터를 가져옵니다."""
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)
        # 네트워크 응답이 실패한 경우 에러 발생
        response.raise_for_status()
        data = response.json()

        # KOBIS API 특성: 인증키 오류 등의 상황에서도 HTTP 200과 함께 faultInfo가 전달됨
        if "faultInfo" in data:
            st.error(
                "❌ API 호출 오류가 발생했습니다. KOBIS_KEY 비밀 금고 설정을 확인해 주세요."
            )
            st.caption(f"오류 메시지: {data['faultInfo'].get('message', '')}")
            return None

        # 박스오피스 데이터 추출
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # 결과 목록이 비어있는 경우 안내
        if not daily_list:
            st.warning(
                "⚠️ 조회된 영화 목록이 없습니다. 아직 당일 집계 전이거나 API 데이터 제공이 지연될 수 있습니다."
            )
            return None

        return daily_list

    except requests.exceptions.RequestException as e:
        st.error(
            "❌ KOBIS 서버 연결에 실패했습니다. 네트워크 상태를 확인해 주세요."
        )
        st.caption(f"상세 오류: {e}")
        return None


# ----------------------------------------------------
# 메인 화면 로직 시작
# ----------------------------------------------------

# 비밀 금고(Secrets)에서 인증키 불러오기
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error(
        "🔒 인증키를 찾을 수 없습니다. Streamlit Cloud의 Secrets 설정에 'KOBIS_KEY'를 추가했는지 확인해 주세요."
    )
    st.stop()

# 어제 날짜 구하기 및 앱 타이틀 표시
target_date = get_yesterday_kst()
formatted_date = (
    f"{target_date[:4]}년 {target_date[4:6]}월 {target_date[6:]}일"
)

st.title("🎬 어제의 영화 박스오피스")
st.text(f"기준일: {formatted_date} (한국 시간)")

# API 데이터 조회
movie_data = fetch_box_office_data(api_key, target_date)

if movie_data:
    # 1. 1위 영화 지표 카드 크게 표시
    top_movie = movie_data[0]
    st.subheader("🥇 어제의 박스오피스 1위")

    # 지표 카드를 3개 컬럼으로 나눠 배치
    col1, col2, col3 = st.columns(3)

    # API 응답값이 모두 문자열이므로 숫자 형식으로 변환하여 천 단위 쉼표 추가
    audi_cnt = int(top_movie.get("audiCnt", 0))
    audi_acc = int(top_movie.get("audiAcc", 0))

    with col1:
        st.metric(label="영화명", value=top_movie.get("movieNm", "-"))
    with col2:
        st.metric(label="어제 관객수", value=f"{audi_cnt:,} 명")
    with col3:
        st.metric(label="누적 관객수", value=f"{audi_acc:,} 명")

    st.divider()

    # 데이터 처리를 위한 데이터프레임(DataFrame) 생성
    df = pd.DataFrame(movie_data)

    # 문자열로 들어온 숫자 컬럼들을 정수(int)형으로 변환
    numeric_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. 관객수 상위 5편 막대그래프
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)

    # 차트에 활용하기 쉽게 영화명과 일일 관객수 컬럼을 추출하여 차트 생성
    chart_data = top_5_df[["movieNm", "audiCnt"]].set_index("movieNm")
    st.bar_chart(chart_data)

    st.divider()

    # 3. 전체 순위 표 출력
    st.subheader("📋 전체 박스오피스 순위")

    # 표에 보여줄 주요 컬럼명 변경 및 가독성 개선
    display_df = df[
        ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
    ].copy()
    display_df.columns = [
        "순위",
        "영화명",
        "개봉일",
        "어제 관객수",
        "누적 관객수",
        "스크린수",
    ]

    # 화면에 표 출력 (인덱스 숫자 번호 제외)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
