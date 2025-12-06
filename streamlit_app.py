import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# 폰트 등록
pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>최고급 AI 실전 시험지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
unit = st.selectbox("단원", ["1. Nice to Meet You", "2. Art Around Us", "3. Life in the Future", "4. Travel", "5. Science", "6. Culture", "7. Global Issues", "8. Success"])
num_questions = st.slider("문제 수", 10, 40, 30, step=5)

if st.button("최고급 실전 시험지 생성 (2단+이름칸+완벽한 문제)", type="primary", use_container_width=True):
    with st.spinner("엠베스트 SE 광사드림 학원 최고급 시험지 만드는 중..."):
        prompt = f"""
        너는 대한민국 최상위 영어 학원의 스타 강사야.
        {grade} 영어 교과서 {unit} 단원의 핵심 문법, 어휘, 독해를 완벽하게 반영해서
        실제 학교 중간고사/기말고사 수준의 최고 퀄리티 문제를 {num_questions}개 만들어줘.

        문제는 반드시 다음과 같은 형식으로만 출력해 (다른 말 절대 하지 마):

        ===문제지===
        1. What is the main idea of the passage?
           ① To explain the history of art
           ② To describe different art forms
           ③ To compare modern and traditional art
           ④ To introduce famous artists

        2. The word "masterpiece" in paragraph 2 is closest in meaning to ______.
           ① failure   ② average work   ③ great work   ④ copy

        ===해답지===
        1. ③ To compare modern and traditional art
           해설: 지문 전체에서 현대 미술과 전통 미술을 비교하고 있습니다.

        2. ③ great work
           해설: masterpiece는 '걸작, 명작'이라는 뜻으로 great work와 가장 가깝습니다.
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        worksheet_text = ""
        answerkey_text = ""
        current = "worksheet"
        for line in raw.split('\n'):
            if "===문제지===" in line:
                current = "worksheet"
                continue
            elif "===해답지===" in line:
                current = "answerkey"
                continue
            if current == "worksheet":
                worksheet_text += line + "\n"
            else:
                answerkey_text += line + "\n"

        def make_exam_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=1.8*cm, rightMargin=1.8*cm)
            styles = getSampleStyleSheet()
            normal = ParagraphStyle('NormalKR', parent=styles['Normal'], fontName='NotoSansKR', fontSize=11.5, leading=20)
            title_style = ParagraphStyle('TitleKR', parent=styles['Title'], fontName='NotoSansKR', fontSize=16, alignment=1, textColor=colors.HexColor("#00008B"))  # 남색

            story = []

            # 헤더
            header = Table([
                ["이름: ____________________", f"{grade} {unit} 문법·독해 평가", "날짜: ________"],
                ["", f"({num_questions}문항)", ""]
            ], colWidths=[6*cm, 9*cm, 5*cm])
            header.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'NotoSansKR'),
                ('FONTSIZE', (0,0), (-1,-1), 11),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f0f0")),
                ('ALIGN', (1,0), (1,0), 'CENTER')
            ]))
            story.append(header)
            story.append(Spacer(1, 20))

            # 문제 2단 (KeepInFrame으로 감싸서 에러 방지, maxHeight 큰 값으로 오버플로우 방지)
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            left_col = []
            right_col = []
            for i, line in enumerate(lines):
                p = Paragraph(line, normal)
                if i % 2 == 0:
                    left_col.append(p)
                    left_col.append(Spacer(1, 18))
                else:
                    right_col.append(p)
                    right_col.append(Spacer(1, 18))

            # KeepInFrame으로 감싸서 에러 방지 (maxHeight 큰 값)
            left_frame = KeepInFrame(maxWidth=9.5*cm, maxHeight=50*cm, content=left_col)
            right_frame = KeepInFrame(maxWidth=9.5*cm, maxHeight=50*cm, content=right_col)

            data = [[left_frame, right_frame]]
            table = Table(data, colWidths=[9.5*cm, 9.5*cm])
            table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(table)

            # 하단
            story.append(Spacer(1, 30))
            story.append(Paragraph("엠베스트 SE 광사드림 학원 │ 대표전화: 010-6248-3405", normal))
            story.append(Paragraph("© 2025 엠베스트 SE 광사드림 학원 All Rights Reserved.", normal))

            doc.build(story)
            buffer.seek(0)
            return buffer

        ws = make_exam_pdf(f"{grade} {unit} 문법·독해 평가", worksheet_text)
        ak = make_exam_pdf(f"{grade} {unit} 정답 및 해설", answerkey_text)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("실전 시험지 PDF", ws, f"엠베스트_{grade}_{unit}_시험지.pdf", "application/pdf")
        with col2:
            st.download_button("정답지 PDF", ak, f"엠베스트_{grade}_{unit}_정답지.pdf", "application/pdf")

        st.success("완성! 이제 진짜 학원 시험지 수준이에요")
        st.balloons()
