import streamlit as st
from openai import OpenAI

# 페이지 이름과 아이콘 설정
st.set_page_config(page_title="인공지능 대화방", page_icon="💬")

st.title("💬 인공지능과 대화하기")
st.write("궁금한 것을 물어보고 나만의 비서와 이야기를 나눠봐!")

# 비밀쇠(API 키)가 있는지 확인하기
if "OPENAI_API_KEY" not in st.secrets:
    st.error(
        "비밀쇠(API Key)가 설정되지 않았어! `secrets.toml` 파일을 확인해줘."
    )
    st.stop()

# 인공지능 연결 준비
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 사이드바 꾸미기 ---
st.sidebar.header("🛠️ 대화 설정하기")

# 1. 말투 고르기
selected_tone = st.sidebar.selectbox(
    "말투 고르기",
    ["친절한 선생님", "시크한 전문가", "되물어보는 조교", "직접 적기"],
)

# 2. 성격 문장 직접 고쳐 쓰기 (직접 적기를 골랐을 때만 나타남)
custom_prompt = ""
if selected_tone == "직접 적기":
    custom_prompt = st.sidebar.text_area(
        "인공지능의 성격을 직접 적어봐!",
        value="너는 유쾌하고 재치 있는 친구야.",
    )

st.sidebar.divider()

# 3. 대화 지우기 버튼
if st.sidebar.button("🗑️ 대화 지우기"):
    st.session_state.messages = []
    st.success("대화 기록이 깨끗하게 지워졌어!")
    st.rerun()

# --- 대화 기록 준비하기 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 화면에 보여주기
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 말투에 따른 성격(시스템 지시사항) 정하기 ---
system_instruction = "너는 친절하고 다정한 선생님이야. 학생의 눈높이에 맞춰서 알기 쉽게 설명해 줘."

if selected_tone == "친절한 선생님":
    system_instruction = (
        "너는 학생들에게 아주 친절하고 다정하게 가르쳐 주는 선생님이야."
    )
elif selected_tone == "시크한 전문가":
    system_instruction = "너는 감정이 없는 시크하고 냉철한 전문가야. 핵심만 정확하고 짧게 짚어줘."
elif selected_tone == "되물어보는 조교":
    system_instruction = (
        "너는 학생을 스스로 생각하게 만드는 조교야. "
        "정답을 바로 알려 주지 말고, 힌트를 하나 준 뒤에 질문을 던져서 되물어봐. "
        "그러다가 학생이 스스로 정답을 말하면, 그때 칭찬해주며 맞았다고 확인해 줘."
    )
elif selected_tone == "직접 적기":
    system_instruction = custom_prompt

# --- 학생이 글을 썼을 때 ---
if prompt := st.chat_input("여기에 물어볼 내용을 적어봐..."):
    # 학생이 보낸 말을 대화 기록에 저장
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # 인공지능에게 보낼 준비 (시스템 성격 + 지금까지의 대화 내용)
    full_messages = [{"role": "system", "content": system_instruction}] + st.session_state.messages

    # 인공지능의 대답 받아오기
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=full_messages,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"앗, 문제가 생겼어! 오류 내용: {e}"
            message_placeholder.markdown(full_response)

    # 인공지능의 대답을 대화 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})
