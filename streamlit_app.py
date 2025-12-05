import os
from io import BytesIO

import streamlit as st
import google.generativeai as genai

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h2>", unsafe_allow_html=True)
st.markdown("---")

grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
if grade == "중1":
    publisher = "동아 (윤정미)"
elif grade == "중2":
    publisher = st.selectbox("출판사", ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)"])
else:
    publisher = "공통 교과서"

units = ["1. Nice to Meet You", "2. Art Around Us", "3. Life in the Future", "4. Travel", "5. Science", "6. Culture", "7. Global Issues", "8. Success"]
unit = st.selectbox("단원 선택", units)

num_questions = st.slider("문제 수", 10, 50, 30, step=5)

# 폰트 파일 경로 (프로젝트 루트에 fonts/NotoSansKR-Regular.ttf 를 넣으세요)
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansKR-Regular.ttf")
FONT_NAME = "NotoSansKR"

def register_font(font_path, font_name=FONT_NAME):
    if not os.path.exists(font_path):
        return False, f"폰트 파일이 없습니다: {font_path}"
    pdfmetrics.registerFont(TTFont(font_name, font_path))
    return True, "OK"

def text_to_pdf_reportlab(text, title, font_name=FONT_NAME):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)
    # 스타일 정의
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleStyle', fontName=font_name, fontSize=18, alignment=1, spaceAfter=6))
    styles.add(ParagraphStyle(name='SubTitle', fontName=font_name, fontSize=14, alignment=1, spaceAfter=12))
    styles.add(ParagraphStyle(name='Body', fontName=font_name, fontSize=12, leading=18))
    # 문서 구성
    story = []
    story.append(Paragraph("엠베스트 SE 광사드림 학원", styles['TitleStyle']))
    story.append(Paragraph(title, styles['SubTitle']))
    story.append(Spacer(1, 6))
    # Preformatted을 사용해 원본 개행/서식 유지
    story.append(Preformatted(text, styles['Body']))
    doc.build(story)
    buffer.seek(0)
    return buffer

if st.button("PDF 문제지 + 해답지 생성 (한글 완벽)", type="primary", use_container_width=True):
    ok, msg = register_font(FONT_PATH)
    if not ok:
        st.error(
            "한글 폰트가 없습니다.\n\n"
            f"프로젝트에 '{FONT_PATH}' 파일을 넣어주세요.\n"
            "권장: Google Fonts에서 'Noto Sans KR'을 다운로드하여 fonts 폴더에 넣으세요."
        )
    else:
        with st.spinner("엠베스트 전용 문제지 만드는 중..."):
            prompt = f"""
            엠베스트 SE 광사드림 학원 전용 문제지
            {grade} {publisher} {unit} 단원, 총 {num_questions}문항
            학교 시험지처럼 위아래 여백 넉넉하고 보기 정렬 깔끔하게
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

            ws_pdf = text_to_pdf_reportlab(worksheet, f"{grade} {unit} 문법·독해 문제 ({num_questions}문항)")
            ak_pdf = text_to_pdf_reportlab(answerkey, f"{grade} {unit} 정답 및 해설")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("문제지 PDF 다운로드", ws_pdf, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
            with col2:
                st.download_button("해답지 PDF 다운로드", ak_pdf, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

            st.success("완성! 한글 완벽 + 인쇄 바로 가능")
            st.balloons()
