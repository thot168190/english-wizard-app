import streamlit as st
import google.generativeai as genai
from io import BytesIO

# 설정
st.set_page_config(page_title="영어 문법 마법사", page_icon="🧙‍♂️", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align: center;'>✍️ 영어 문법 마법사</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>교과서 단원에 딱 맞는 문제지 + 해답지를 30초 안에 만들어 드려요!</p>", unsafe_allow_html=True)
st.markdown("---")

# 학년 & 단원
col1, col2 = st.columns(2)
with col1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
with col2:
    textbook_units = {
        "중1": ["1. Nice to Meet You", "2. What Do You Like?", "3. My Day", "4. My Family", "5. School Life", "6. Hobbies"],
        "중2": ["1. Daily Life", "2. Food", "3. Weather", "4. Vacation", "5. Shopping", "6. Health"],
        "중3": ["1. Welcome to Korea", "2. Life in the Future", "3. Heroes", "4. Travel", "5. Science and Technology", "6. Culture"],
        "고1": ["1. Relationships", "2. Health", "3. Technology", "4. Environment", "5. Success", "6. Pop Culture"],
        "고2": ["1. Decisions", "2. Leisure", "3. Global Issues", "4. Values", "5. Media", "6. Challenges"],
        "고3": ["1. Economy", "2. Ethics", "3. Art", "4. History", "5. Literature", "6. Philosophy"],
    }
    units = textbook_units.get(grade, [f"Lesson {i}" for i in range(1, 16)])
    unit = st.selectbox("단원 선택", units)

# 옵션
col3, col4, col5 = st.columns(3)
with col3:
    num_questions = st.slider("문제 수", 10, 50, 30, step=5)
with col4:
    problem_type = st.multiselect("문제 유형", 
        ["빈칸 채우기", "어법 판단", "순서 배열", "문장 완성", "오류 고치기", "어휘 선택", "독해 지문"],
        default=["빈칸 채우기", "어법 판단", "순서 배열"])
with col5:
    difficulty = st.radio("난이도", ["쉬움", "보통", "어려움"])

if st.button("🚀 문제지 만들기", type="primary", use_container_width=True):
    with st.spinner("마법사가 열심히 문제 만드는 중..."):
        prompt = f"""
        {grade} 영어 교과서 '{unit}' 단원 내용을 정확히 반영해서,
        난이도: {difficulty}
        한국 중고등학생 수준에 딱 맞는 고퀄리티 영어 문법·독해 문제를 {num_questions}개 만들어줘.
        유형은 {', '.join(problem_type)}을 골고루 섞고,
        각 문제마다 정답과 해설을 달아줘.
        출력은 아래 형식으로만 해줘 (마크다운 사용 금지, 순수 텍스트로):

        ===문제지===
        제목: {grade} {unit} 문법/독해 문제 ({num_questions}문항)

        1. 문제 내용
            (a)  (b)  (c)  (d)

        2. ...

        ===해답지===
        1. 정답: (b)   해설: ...

        2. 정답: (c)   해설: ...
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw_text = response.text

        # 문제지 / 해답지 분리
        if "===문제지===" in raw_text and "===해답지===" in raw_text:
            worksheet = raw_text.split("===해답지===")[0].replace("===문제지===", "").strip()
            answerkey = raw_text.split("===해답지===")[1].strip()
        else:
            worksheet = raw_text
            answerkey = "해답지를 생성하지 못했습니다."

        # 2단 레이아웃으로 예쁘게 출력
        st.success("완성!")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### 📝 문제지")
            st.markdown(f"```{worksheet}```")
            buffer = BytesIO()
            buffer.write(worksheet.encode('utf-8'))
            st.download_button("📄 문제지 다운로드", buffer, f"{grade}_{unit}_문제지.txt", "text/plain")
        with col_b:
            st.markdown("### 🔑 해답지")
            st.markdown(f"```{answerkey}```")
            buffer2 = BytesIO()
            buffer2.write(answerkey.encode('utf-8'))
            st.download_button("🔒 해답지 다운로드", buffer2, f"{grade}_{unit}_해답지.txt", "text/plain")

        st.balloons()
