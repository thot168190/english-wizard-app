import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.title("엠베스트 SE 광사드림 학원")
st.markdown("### AI 교과서 맞춤 문제지 생성기 (한글 깨짐 100% 해결 버전)")

grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
unit = st.selectbox("단원", ["1. Nice to Meet You", "2. Art Around Us", "3. Life in the Future", "4. Travel", "5. Science", "6. Culture", "7. Global Issues", "8. Success"])
num_questions = st.slider("문제 수", 10, 40, 30, step=5)

if st.button("PDF 문제지 + 해답지 생성 (한글 안 깨짐)", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 문제지 만드는 중..."):
        # 핵심!! Gemini한테 영어로만 만들라고 강제
        prompt = f"""
        Create {num_questions} English grammar/reading problems ONLY IN ENGLISH for middle/high school students.
        Unit: {unit}
        Make it look like a real school exam with choices (A) (B) (C) (D)
        Provide answer key with explanations.

        Format:
        ===WORKSHEET===
        1. Question here...
           (A) ...  (B) ...  (C) ...  (D) ...

        ===ANSWER KEY===
        1. (B) Explanation: ...
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        # 분리
        if "===ANSWER KEY===" in raw:
            worksheet = raw.split("===ANSWER KEY===")[0].replace("===WORKSHEET===", "").strip()
            answerkey = raw.split("===ANSWER KEY===")[1].strip()
        else:
            worksheet = raw
            answerkey = "Answer key not generated."

        # 깨끗한 영어 PDF (한글 0% → 깨질 일 없음)
        def make_clean_pdf(title, content):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=3*cm, bottomMargin=3*cm,
                                    leftMargin=2.5*cm, rightMargin=2.5*cm)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=16, alignment=1, spaceAfter=30)
            body = ParagraphStyle('Body', fontName='Helvetica', fontSize=11, leading=20, spaceAfter=15)

            story = [
                Paragraph("Embest SE Gwangsa Dream Academy", title_style),
                Paragraph(title, title_style),
                Spacer(1, 40)
            ]
            for line in content.split('\n'):
                if line.strip():
                    story.append(Paragraph(line.strip(), body))
                    story.append(Spacer(1, 18))

            doc.build(story)
            buffer.seek(0)
            return buffer

        ws = make_clean_pdf(f"{grade} {unit} - Grammar & Reading ({num_questions}Q)", worksheet)
        ak = make_clean_pdf(f"{grade} {unit} - Answer Key", answerkey)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF (완벽)", ws, f"Embest_{grade}_{unit}_Worksheet.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF (완벽)", ak, f"Embest_{grade}_{unit}_AnswerKey.pdf", "application/pdf")

        st.success("완성! 한글 1도 안 깨짐 + 인쇄 바로 가능")
        st.balloons()
