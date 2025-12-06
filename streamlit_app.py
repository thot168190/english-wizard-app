import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# 깃허브에 폰트 있으니까 바로 등록 (이게 핵심!)
pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# 학년 선택
grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])

# 출판사 선택
if grade == "중1":
    publisher = "동아 (윤정미)"
    st.info("동아 (윤정미)")
elif grade == "중2":
    publisher = st.selectbox("출판사", ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)"])
else:
    publisher = "공통 교과서"
    st.info(publisher)

# 단원 선택 (8과 정확)
units = ["1. Nice to Meet You", "2. How Are You?", "3. My Day", "4. My Family", "5. At School", "6. Let's Eat!", "7. Art Around Us", "8. Seasons and Weather"]
unit = st.selectbox("단원 선택", units)

col1, col2 = st.columns(2)
with col1:
    num_questions = st.slider("문제 수", 10, 50, 30, step=5)
with col2:
    difficulty = st.radio("난이도", ["쉬움", "보통", "어려움"])

if st.button("PDF 문제지 + 해답지 생성", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 문제지 만드는 중..."):
        prompt = f"""
        엠베스트 SE 광사드림 학원 전용 문제지
        {grade} {publisher} {unit} 단원
        난이도: {difficulty}, 총 {num_questions}문항
        학교 시험지처럼 위아래 여백 넉넉하고 보기 정렬 깔끔하게 만들어줘.
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

        # PDF 생성 (NotoSansKR 폰트로 한글 완벽)
        def make_pdf(title, content):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=3.5*cm, bottomMargin=3*cm,
                                    leftMargin=2.5*cm, rightMargin=2.5*cm)
            styles = getSampleStyleSheet()
            body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='NotoSansKR', fontSize=12, leading=24, spaceAfter=20)
            title_style = ParagraphStyle('Title', parent=styles['Title'], fontName='NotoSansKR', fontSize=18, alignment=1, spaceAfter=30)

            story = [
                Paragraph("엠베스트 SE 광사드림 학원", title_style),
                Paragraph(title, title_style),
                Spacer(1, 40)
            ]

            for line in content.split('\n'):
                if line.strip():
                    story.append(Paragraph(line.strip(), body_style))
                    story.append(Spacer(1, 25))

            doc.build(story)
            buffer.seek(0)
            return buffer

        ws = make_pdf(f"{grade} {unit} 문법·독해 문제 ({num_questions}문항)", worksheet)
        ak = make_pdf(f"{grade} {unit} 정답 및 해설", answerkey)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF 다운로드", ws, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF 다운로드", ak, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.success("완성! 한글 완벽 + 인쇄 바로 가능")
        st.balloons()

st.caption("© 2025 엠베스트 SE 광사드림 학원 전용 AI 문제 생성기")
