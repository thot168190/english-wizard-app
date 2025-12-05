import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# 한글 폰트 직접 등록 (이게 핵심!)
pdfmetrics.registerFont(TTFont("NanumGothic", "https://github.com/soonhokong/NanumGothic/raw/main/NanumGothic-Regular.ttf"))

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# 학년, 출판사, 단원 선택 (이전 그대로)

if st.button("학교 시22시험지 PDF 생성", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 문제지 만드는 중..."):
        # 프롬프트 (이전 그대로)
        prompt = f"{grade} {publisher} {unit} 단원, {num_questions}문항, {difficulty} 난이도..."
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        parts = raw.split("===해답지===")
        worksheet = parts[0].replace("===문제지===", "").strip()
        answerkey = parts[1].strip() if len(parts) > 1 else ""

        # 한글 완벽 + 학교 시험지 스타일 PDF
        def create_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=3*cm, leftMargin=2.5*cm, rightMargin=2.5*cm)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Korean', fontName="NanumGothic", fontSize=12, leading=22, alignment=0, spaceAfter=18))
            styles.add(ParagraphStyle(name='Title', fontName="NanumGothic", fontSize=18, alignment=1, spaceAfter=30))

            story = []
            story.append(Paragraph("엠베스트 SE 광사드림 학원", styles["Title"]))
            story.append(Paragraph(title, styles["Title"]))
            story.append(Spacer(1, 40))

            for line in content.split('\n'):
                if line.strip():
                    if is_answer:
                        story.append(Paragraph(f"<font color='red'><b>{line.strip()}</b></font>", styles["Korean"]))
                    else:
                        story.append(Paragraph(line.strip(), styles["Korean"]))
                    story.append(Spacer(1, 25))

            doc.build(story)
            buffer.seek(0)
            return buffer

        ws_pdf = create_pdf(f"{grade} {unit} 문법·독해 문제 ({num_questions}문항)", worksheet)
        ak_pdf = create_pdf(f"{grade} {unit} 정답 및 해설", answerkey, is_answer=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF 다운로드", ws_pdf, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF 다운로드", ak_pdf, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.success("완성! 한글도 예쁘고 인쇄 바로 가능")
        st.balloons()
