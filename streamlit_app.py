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

# 폰트 등록 (너 깃허브에 있음)
pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>최고급 AI 실전 시험지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# 세션 상태로 PDF 저장 (다운로드 후에도 사라지지 않음)
if "ws_pdf" not in st.session_state:
    st.session_state.ws_pdf = None
if "ak_pdf" not in st.session_state:
    st.session_state.ak_pdf = None

grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
unit = st.selectbox("단원", ["1. Nice to Meet You", "2. Art Around Us", "3. Life in the Future", "4. Travel", "5. Science", "6. Culture", "7. Global Issues", "8. Success"])
num_questions = st.slider("문제 수", 10, 40, 30, step=5)

if st.button("최고급 실전 시험지 생성 (완전 완벽)", type="primary", use_container_width=True):
    with st.spinner("최고급 시험지 생성 중..."):
        prompt = f"""
        엠베스트 SE 광사드림 학원 실전 시험지
        {grade} {unit} 단원, 총 {num_questions}문항
        최고 퀄리티로 만들어줘.

        출력 형식:

        ===문제지===
        1. 다음 영영 풀이가 설명하는 단어로 가장 적절한 것은?
           ① tradition ② custom ③ culture ④ festival

        2. 다음 문장의 빈칸에 들어갈 말로 가장 적절한 것은?
           Many Koreans still wear traditional clothes called Hanbok on special ______ like Chuseok and Seollal.
           ① events ② parties ③ holidays ④ customs

        ===해답지===
        1. ③ culture
           해설: An accepted way of behaving or doing things in a particular society or community.

        2. ③ holidays
           해설: Many Koreans still wear traditional clothes called Hanbok on special holidays like Chuseok and Seollal.
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        # 정확한 파싱
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

        def make_perfect_pdf(title, content):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=1.8*cm, rightMargin=1.8*cm)
            styles = getSampleStyleSheet()
            normal = ParagraphStyle('NormalKR', parent=styles['Normal'], fontName='NotoSansKR', fontSize=11.5, leading=20)
            title_style = ParagraphStyle('TitleKR', parent=styles['Title'], fontName='NotoSansKR', fontSize=16, alignment=1, textColor=colors.HexColor("#00008B"))

            story = []

            # 첫 번째 사진처럼 완벽한 헤더
            header = Table([
                ["이름: ____________________", f"<font size=14 color='#00008B'><b>{grade} {unit} 문법·독해 평가</b></font>", "날짜: ________"],
                ["", f"({num_questions}문항)", """, ""]
            ], colWidths=[6*cm, 9*cm, 5*cm])
            header.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'NotoSansKR'),
                ('FONTSIZE', (0,0), (-1,-1), 11),
                ('GRID', (0,0), (-1,-1), 0.7, colors.darkblue),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e6f2ff")),
                ('ALIGN', (1,0), (1,0), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            story.append(header)
            story.append(Spacer(1, 20))

            # 문제 전체 그대로 출력 (줄바꿈만 잘 처리)
            for line in content.split('\n'):
                if line.strip():
                    story.append(Paragraph(line.strip(), normal))
                    story.append(Spacer(1, 18))

            # 하단 학원명
            story.append(Spacer(1, 30))
            story.append(Paragraph("엠베스트 SE 광사드림 학원 │ 대표전화: 010-6248-3405", normal))
            story.append(Paragraph("© 2025 엠베스트 SE 광사드림 학원 All Rights Reserved.", normal))

            doc.build(story)
            buffer.seek(0)
            return buffer

        # 세션에 저장 → 다운로드 후에도 사라지지 않음
        st.session_state.ws_pdf = make_perfect_pdf(f"{grade} {unit} 문법·독해 평가", worksheet_text)
        st.session_state.ak_pdf = make_perfect_pdf(f"{grade} {unit} 정답 및 해설", answerkey_text)

        st.success("완성! 이제 진짜 학원 시험지 수준이에요")
        st.balloons()

# 다운로드 버튼 (항상 보임)
col1, col2 = st.columns(2)
with col1:
    if st.session_state.ws_pdf:
        st.download_button("실전 시험지 PDF", st.session_state.ws_pdf, f"엠베스트_{grade}_{unit}_시험지.pdf", "application/pdf")
    else:
        st.info("문제지를 먼저 생성해주세요")
with col2:
    if st.session_state.ak_pdf:
        st.download_button("정답지 PDF", st.session_state.ak_pdf, f"엠베스트_{grade}_{unit}_정답지.pdf", "application/pdf")
    else:
        st.info("문제지를 먼저 생성해주세요")

st.caption("© 2025 엠베스트 SE 광사드림 학원")
