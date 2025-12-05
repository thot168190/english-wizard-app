import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="영어 문법 마법사", page_icon="🧙‍♂️", layout="wide")

# Secrets에서 키 자동 불러오기 (키 입력창 완전 삭제!)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 제목
st.title("✍️ AI 교과서 내용 일치 문제 생성기")

# 학년 선택
grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "중1", "중2", "중3", "고1", "고2", "고3"])

# 교과서 단원 (필요하면 더 추가해도 됨)
textbook_units = {
    "중1": ["1. Nice to Meet You", "2. What Do You Like?", "3. My Day", "4. My Family", "5. School Life", "6. Hobbies"],
    "중2": ["1. Daily Life", "2. Food", "3. Weather", "4. Vacation", "5. Shopping", "6. Health"],
    "중3": ["1. Welcome to Korea", "2. Life in the Future", "3. Heroes", "4. Travel", "5. Science", "6.
