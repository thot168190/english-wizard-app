import streamlit as st
import google.generativeai as genai
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 한글 폰트 등록 (Streamlit Cloud에 기본 포함된 폰트 사용)
pdfmetrics.registerFont(TTFont("Malgun", "malgun.ttf"))  # Windows 기본 폰트
# 만약 위가 안 되면 아래 주석 풀고 사용
# pdfmetrics.registerFont(TTFont("NanumGothic", "NanumGothic.ttf"))

st.set_page_config(page_title="엠베스트 SE 광사드림", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# (학년, 출판사, 단원 선택은 그대로 생략 - 이전 코드와 동일)

# ... (기존 선택 UI 코드 그대로) ...

if st.button("PDF 문제지 생성하기", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 PDF 만드는 중..."):
        # Gemini 프롬프트 (이전과 동일)
        prompt = f"{grade} {publisher} {unit} 단원, {num_questions}문항, {difficulty} 난이도..."
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        parts = raw.split("===해답지===")
        worksheet = parts[0].replace("===문제지===", "").strip()
        answerkey = parts[1].strip() if len(parts) > 1 else ""

        # 한글 지원 PDF 생성 함수
        def create_korean_pdf(title, content):
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            c.setFont("Malgun", 12)  # 한글 폰트 적용

            # 제목
            c.setFont("Malgun", 18)
            c.drawCentredString(width/2, height - 2*cm, "엠베스트 SE 광사드림 학원")
            c.setFont("Malgun", 14)
            c.drawCentredString(width/2, height - 3*cm, title)

            # 내용
            c.setFont("Malgun", 11)
            y = height - 5*cm
            for line in content.split('\n'):
                if line.strip():
                    c.drawString(2*cm, y, line.strip())
                    y -= 15
                    if y < 2*cm:
                        c.showPage()
                        y = height - 2*cm

            c.save()
            buffer.seek(0)
            return buffer

        worksheet_pdf = create_korean_pdf(f"{grade} {unit} 문제지", worksheet)
        answerkey_pdf = create_korean_pdf(f"{grade} {unit} 해답지", answerkey)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF (한글 완벽)", worksheet_pdf, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF (한글 완벽)", answerkey_pdf, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.success("한글 완벽 PDF 완성!")
        st.balloons()
