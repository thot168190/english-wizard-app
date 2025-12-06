import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# 너 깃허브에 폰트 있으니까 바로 등록
pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
if grade == "중1":
    publisher = "동아 (윤정미)"
elif grade == "중2":
    publisher = st.selectbox("출판사", ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)"])
else:
    publisher = "공통 교과서"

unit = st.selectbox("단원 선택", ["1. Nice to Meet You", "2. Art Around Us", "3. Life in the Future", "4. Travel", "5. Science", "6. Culture", "7. Global Issues", "8. Success"])
num_questions = st.slider("문제 수", 10, 50, 30, step=5)

if st.button("실제 시험지 PDF 생성 (2단+이름칸+학원명)", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 실전 시험지 만드는 중..."):
        prompt = f"""
        엠베스트 SE 광사드림 학원 실전 문제지
        {grade} {publisher} {unit} 단원, 총 {num_questions}문항
        학교 시험지처럼 2단으로 구성하고 보기 정렬 깔끔하게
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

        def make_exam_pdf(title, content):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=1.8*cm, rightMargin=1.8*cm)
            styles = getSampleStyleSheet()
            normal = ParagraphStyle('NormalKR', parent=styles['Normal'], fontName='NotoSansKR', fontSize=11, leading=18, spaceAfter=12)
            title_style = ParagraphStyle('TitleKR', parent=styles['Title'], fontName='NotoSansKR', fontSize=16, alignment=1, spaceAfter=20)
            small = ParagraphStyle('Small', fontName='NotoSansKR', fontSize=9, textColor=colors.grey)

            story = []

            # 헤더 테이블 (이름, 학번, 날짜)
            header_data = [
                ["이름: ____________________", f"{grade} {unit} 문법·독해 평가", "날짜: ________"],
                ["", f"({num_questions}문항)", ""]
            ]
            header_table = Table(header_data, colWidths=[6*cm, 9*cm, 5*cm])
            header_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'NotoSansKR'),
                ('FONTSIZE', (0,0), (-1,-1), 11),
                ('ALIGN', (1,0), (1,0), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f0f0"))
            ]))
            story.append(header_table)
            story.append(Spacer(1, 20))

            # 문제 내용 2단으로 분할
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            left_col = []
            right_col = []
            for i, line in enumerate(lines):
                para = Paragraph(line, normal)
                if i % 2 == 0:
                    left_col.append(para)
                    left_col.append(Spacer(1, 15))
                else:
                    right_col.append(para)
                    right_col.append(Spacer(1, 15))

            # 2단 테이블
            data = [[left_col, right_col]]
            table = Table(data, colWidths=[9.5*cm, 9.5*cm])
            table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(table)

            # 페이지 하단 학원명
            story.append(Spacer(1, 30))
            story.append(Paragraph("엠베스트 SE 광사드림 학원 │ 대표전화: 010-XXXX-XXXX", small))
            story.append(Paragraph("© 2025 엠베스트 SE 광사드림 학원 All Rights Reserved.", small))

            doc.build(story)
            buffer.seek(0)
            return buffer

        # 여기서 {{grade}}처럼 중괄호 2개 써서 f-string 충돌 해결!
        ws_title = f"{grade} {unit} 문법·독해 평가 ({num_questions}문항)"
        ws = make_exam_pdf(ws_title, worksheet)
        ak = make_exam_pdf(f"{grade} {unit} 정답 및 해설", answerkey)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("실전 시험지 PDF 다운로드", ws, f"엠베스트_{grade}_{unit}_시험지.pdf", "application/pdf")
        with col2:
            st.download_button("정답지 PDF 다운로드", ak, f"엠베스트_{grade}_{unit}_정답지.pdf", "application/pdf")

        st.success("완성! 실제 학원 시험지랑 똑같아요")
        st.balloons()
