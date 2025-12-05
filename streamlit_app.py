import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="영어 문법 마법사", page_icon="🧙‍♂️", layout="wide")

# Secrets에서 키 자동 불러오기 → 키 입력창 완전 삭제
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.title("AI 교과서 내용 일치 문제 생성기")

# 학년 선택
grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "중1", "중2", "중3", "고1", "고2", "고3"])

# 교과서 단원 목록 (모두 정상적으로 닫힘!)
textbook_units = {
    "중1": ["1. Nice to Meet You", "2. What Do You Like?", "3. My Day", "4. My Family", "5. School Life", "6. Hobbies"],
    "중2": ["1. Daily Life", "2. Food", "3. Weather", "4. Vacation", "5. Shopping", "6. Health"],
    "중3": ["1. Welcome to Korea", "2. Life in the Future", "3. Heroes", "4. Travel", "5. Science and Technology", "6. Culture"],
    "고1": ["1. Relationships", "2. Health", "3. Technology", "4. Environment", "5. Success", "6. Pop Culture"],
    "고2": ["1. Decisions", "2. Leisure", "3. Global Issues", "4. Values", "5. Media", "6. Challenges"],
    "고3": ["1. Economy", "2. Ethics", "3. Art", "4. History", "5. Literature", "6. Philosophy"],
}

# 선택된 학년에 맞는 단원 리스트
units = textbook_units.get(grade, [f"Lesson {i}" for i in range(1, 16)])
unit = st.selectbox("단원 선택", units)

# 문제 수 + 유형 선택
col1, col2 = st.columns(2)
with col1:
    num_questions = st.slider("문제 수", 5, 50, 30, step=5)
with col2:
    problem_type = st.multiselect("문제 유형", 
        ["빈칸 채우기", "어법 판단", "순서 배열", "문장 완성", "오류 고치기", "어휘 선택", "독해 지문"],
        default=["빈칸 채우기", "어법 판단", "순서 배열"])

# 생성 버튼
if st.button("문제 생성하기", type="primary"):
    with st.spinner(f"{num_questions}개 문제 생성 중..."):
        prompt = f"""
        {grade} 영어 교과서 '{unit}' 단원 내용을 정확히 반영해서
        한국 중고등학생 수준에 맞는 고퀄리티 영어 문법·독해 문제를 {num_questions}개 만들어줘.
        문제 유형은 {', '.join(problem_type)}을 골고루 섞고,
        각 문제마다 정답과 친절한 해설도 꼭 달아줘!
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        st.markdown(response.text)
