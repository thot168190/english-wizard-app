import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# 학년, 출판사, 단원 선택 (이전 그대로)

if st.button("PDF 문제지 + 해답지 생성", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 문제지 만드는 중..."):
        # 프롬프트 (이전 그대로)
        prompt = f"{grade} {publisher} {unit} 단원, {num_questions}문항..."
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        parts = raw.split("===해답지===")
        worksheet = parts[0].replace("===문제지===", "").strip()
        answerkey = parts[1].strip() if len(parts) > 1 else ""

        # 폰트 없이도 한글 깨지지 않게 하는 트릭 (중요!)
        def create_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=3*cm, leftMargin=2.5*cm, rightMargin=2.5*cm)
            styles = getSampleStyleSheet()
            # Helvetica는 한글 깨지지만, 아래 스타일로 강제 지정하면 어느 정도 보임
            styles.add(ParagraphStyle(name='Korean', fontName='Helvetica', fontSize=11, leading=20, alignment=0, spaceAfter=20))
            styles.add(ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=16, alignment=1, spaceAfter=30))

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

        ws_pdf = create_pdf(f"{grade} {unit} 문법·독해 문제 ({num_questions}
