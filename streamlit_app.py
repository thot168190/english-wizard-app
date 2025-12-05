import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="🏆", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# 학년 선택
grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])

# 출판사 선택
if grade == "중1":
    publisher = "동아 (윤정미)"
elif grade == "중2":
    publisher = st.selectbox("출판사", ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)"])
else:
    publisher = "기본 교과서"

# 단원 8과 정확
units = {
    "중1": ["1. Nice to Meet You", "2. How Are You?", "3. My Day", "4. My Family", "5. At School", "6. Let's Eat!", "7. My Favorite Things", "8. Seasons and Weather"],
    "중2": ["1. Suit Your Taste!", "2. Half a World Away", "3. I Wonder Why", "4. The Art of Living", "5. Explore Your Feelings", "6. Doors to the Wild", "7. Art Around Us", "8. Changes Ahead"],
    "중3": ["1. Express Your Feelings", "2. Let's Make Our Town Better", "3. Heroes Around Us", "4. Let's Travel", "5. Science and Us", "6. Korean Culture", "7. Global Issues", "8. Peace and Cooperation"],
    "고1": ["1. People Around Us", "2. Health and Lifestyle", "3. Science and Technology", "4. Environment", "5. Success and Happiness", "6. Popular Culture", "7. Media and Information", "8. Challenges in Life"],
    "고2": ["1. Life Choices", "2. Leisure and Hobbies", "3. Global Issues", "4. Values and Beliefs", "5. Media and Information", "6. Challenges in Life", "7. Art and Literature", "8. History and Culture"],
    "고3": ["1. Economy and Society", "2. Ethics and Philosophy", "3. Art and Literature", "4. History and Culture", "5. Science and Future", "6. Global Citizenship", "7. Relationships", "8. Success"]
}

unit = st.selectbox("단원 선택", units.get(grade, ["Unit 1"] * 8))

# 옵션
col1, col2 = st.columns(2)
with col1:
    num_questions = st.slider("문제 수", 10, 50, 30, step=5)
with col2:
    difficulty = st.radio("난이도", ["Easy", "Medium", "Hard"])

if st.button("Generate PDF Worksheet + Answer Key", type="primary", use_container_width=True):
    with st.spinner("Creating..."):
        prompt = f"""
        Embest SE Gwangsa Dream Academy worksheet
        {grade} {publisher} {unit} unit
        Difficulty: {difficulty}, Total {num_questions} questions
        Make like school exam with ample top/bottom margins and clean alignment for choices ①②③④
        Output format:

        ===Worksheet===
        1. Problem content
           ① Choice1  ② Choice2  ③ Choice3  ④ Choice4

        ===Answer Key===
        1. Answer: ② Explanation: ...
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        parts = raw.split("===Answer Key===")
        worksheet = parts[0].replace("===Worksheet===", "").strip()
        answerkey = parts[1].strip() if len(parts) > 1 else ""

        def make_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=3*cm, leftMargin=2.5*cm, rightMargin=2.5*cm)
            styles = getSampleStyleSheet()
            body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=12, leading=22, spaceAfter=20)
            title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=18, alignment=1, spaceAfter=30)

            story = [
                Paragraph("Embest SE Gwangsa Dream Academy", title_style),
                Paragraph(title, title_style),
                Spacer(1, 40)
            ]

            for line in content.split('\n'):
                if line.strip():
                    if is_answer:
                        story.append(Paragraph(f"<font color='red'><b>{line.strip()}</b></font>", body_style))
                    else:
                        story.append(Paragraph(line.strip(), body_style))
                    story.append(Spacer(1, 25))

            doc.build(story)
            buffer.seek(0)
            return buffer

        ws = make_pdf(f"{grade} {unit} Grammar/Reading Problem ({num_questions} Q)", worksheet)
        ak = make_pdf(f"{grade} {unit} Answer Key", answerkey, is_answer=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Worksheet PDF", ws, f"Embest_{grade}_{unit}_Worksheet.pdf", "application/pdf")
        with col2:
            st.download_button("Answer Key PDF", ak, f"Embest_{grade}_{unit}_AnswerKey.pdf", "application/pdf")

        st.success("완성! 바로 인쇄하세요 (영어 중심으로 깨짐 방지)")
        st.balloons()
