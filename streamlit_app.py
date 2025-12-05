import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

st.set_page_config(page_title="Embest SE Gwangsa Dream Academy", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 타이틀 (한글 따옴표 문제 없애기 위해 영어로)
st.markdown("<h1 style='text-align: center; color: #1E40AF; font-size: 50px;'>Embest SE Gwangsa Dream Academy</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #374151;'>AI Textbook Customized Problem Generator</h3>", unsafe_allow_html=True)
st.markdown("---")

# 학년 & 출판사 & 단원
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    grade = st.selectbox("Grade", ["Middle 1", "Middle 2", "Middle 3", "High 1", "High 2", "High 3"])
with col2:
    if grade == "Middle 1":
        publisher = "Dong-A (Yoon Jung-mi)"
        st.info(publisher)
    elif grade == "Middle 2":
        publisher = st.selectbox("Publisher", ["Cheonjae (Jeong Sa-yeol)", "Cheonjae (Lee Jae-young)", "Bisaeng (Kim Jin-wan)"])
    else:
        publisher = "Standard Textbook"
        st.info(publisher)
with col3:
    textbook_units = {
        "Middle 1": ["1. Nice to Meet You", "2. What Do You Like?", "3. My Day", "4. My Family", "5. School Life", "6. Hobbies"],
        "Middle 2": ["1. Daily Life", "2. Food", "3. Weather", "4. Vacation", "5. Shopping", "6. Health"],
        "Middle 3": ["1. Welcome to Korea", "2. Life in the Future", "3. Heroes", "4. Travel", "5. Science and Technology", "6. Culture"],
        "High 1": ["1. Relationships", "2. Health", "3. Technology", "4. Environment", "5. Success", "6. Pop Culture"],
        "High 2": ["1. Decisions", "2. Leisure", "3. Global Issues", "4. Values", "5. Media", "6. Challenges"],
        "High 3": ["1. Economy", "2. Ethics", "3. Art", "4. History", "5. Literature", "6. Philosophy"],
    }
    units = textbook_units.get(grade, [f"Lesson {i}" for i in range(1, 16)])
    unit = st.selectbox("Unit", units)

col4, col5, col6 = st.columns(3)
with col4:
    num_questions = st.slider("Number of Questions", 10, 50, 30, step=5)
with col5:
    problem_type = st.multiselect("Problem Types", 
        ["Fill in the Blanks", "Grammar Judgment", "Sequence Arrangement", "Sentence Completion", "Error Correction", "Vocabulary Choice", "Reading Comprehension"],
        default=["Fill in the Blanks", "Grammar Judgment", "Sequence Arrangement"])
with col6:
    difficulty = st.radio("Difficulty", ["Easy", "Medium", "Hard"])

if st.button("Generate School-Style PDF Worksheet", type="primary", use_container_width=True):
    with st.spinner("Creating school-style PDF with ample margins..."):
        prompt = f"""
        Embest SE Gwangsa Dream Academy worksheet
        Grade: {grade} / Publisher: {publisher} / Unit: {unit} / Difficulty: {difficulty}
        Create {num_questions} high-quality English grammar/reading problems based on the unit content.
        Mix types: {', '.join(problem_type)}
        Output format (no markdown):

        ===Worksheet===
        1. Problem content with ample space for answers
           ① Choice A  ② Choice B  ③ Choice C  ④ Choice D

        ===Answer Key===
        1. Answer: ② Explanation: ...

        Make it look like a school exam with generous top/bottom margins.
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw_text = response.text

        parts = raw_text.split("===Answer Key===")
        worksheet = parts[0].replace("===Worksheet===", "").strip
