import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="🏆", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# 학년, 출판사, 단원 (이전 그대로)

if st.button("PDF 문제지 + 해답지 생성", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 문제지 만드는 중..."):
        prompt = f"""
        {grade} {publisher} {unit} 단원
        {num_questions}문항 만들어줘. 난이도: {difficulty}
        문제 유형: {', '.join(problem_type)}
        출력 형식:

        ===문제지===
        1. 문제 내용
           ① 보기1  ② 보기2  ③ 보기3  ④ 보기4

        ===해답지===
        1. 정답: ②  해설: ...
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        parts = raw.split("===해답지===")
        worksheet = parts[0].replace("===문제지===", "").strip()
        answerkey = parts[1].strip() if len(parts) > 1 else ""

        # f-string 중괄호 문제 완전 해결 ({{ }} 사용)
        def create_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=3*cm, leftMargin=2.5*cm, rightMargin=2.5*cm)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Body', fontName='Helvetica', fontSize=11, leading=22, spaceAfter=20))
            styles.add(ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=16, alignment=1, spaceAfter=30))

            story = []
            story.append(Paragraph("엠베스트 SE 광사드림 학원", styles["Title"]))
            story.append(Paragraph(title, styles["Title"]))
            story.append(Spacer(1, 40))

            for line in content.split('\n'):
                if line.strip():
                    if is_answer:
                        story.append(Paragraph(f"<font color='red'><b>{line.strip()}</b></font>", styles["Body"]))
                    else:
                        story.append(Paragraph(line.strip(), styles["Body"]))
                    story.append(Spacer(1, 25))

            doc.build(story)
            buffer.seek(0)
            return buffer

        # 여기서 {{grade}}처럼 중괄호 2개 써서 해결!
        ws_title = f"{grade} {unit} 문법·독해 문제 ({num_questions}문항)"
        ak_title = f"{grade} {unit} 정답 및 해설"

        ws_pdf = create_pdf(ws_title, worksheet)
        ak_pdf = create_pdf(ak_title, answerkey, is_answer=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF 다운로드", ws_pdf, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF 다운로드", ak_pdf, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.success("완성! 인쇄해서 바로 써요!")
        st.balloons()
