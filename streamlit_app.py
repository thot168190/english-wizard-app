import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO

st.set_page_config(page_title="엠베스트 SE 광사드림", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 타이틀 멋지게
st.markdown("""
<h1 style='text-align: center; color: #1E40AF; font-size: 50px; margin-bottom: 0;'>엠베스트 SE 광사드림 학원</h1>
<h3 style='text-align: center; color: #374151; margin-top: 10px;'>AI 교과서 맞춤 문제 생성기</h3>
<hr style='border: 2px solid #1E40AF; width: 50%;'>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
with col2:
    if grade == "중1":
        publisher = "동아 (윤정미)"
        st.info(publisher)
    elif grade == "중2":
        publisher = st.selectbox("출판사", ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)"])
    else:
        publisher = "기본 교과서"
        st.info(publisher)
with col3:
    textbook_units = {
        "중1": ["1. Nice to Meet You", "2. What Do You Like?", "3. My Day", "4. My Family", "5. School Life", "6. Hobbies"],
        "중2": ["1. Daily Life", "2. Food", "3. Weather", "4. Vacation", "5. Shopping", "6. Health"],
        "중3": ["1. Welcome to Korea", "2. Life in the Future", "3. Heroes", "4. Travel", "5. Science", "6. Culture"],
        "고1": ["1. Relationships", "2. Health", "3. Technology", "4. Environment", "5. Success", "6. Pop Culture"],
        "고2": ["1. Decisions", "2. Leisure", "3. Global Issues", "4. Values", "5. Media", "6. Challenges"],
        "고3": ["1. Economy", "2. Ethics", "3. Art", "4. History", "5. Literature", "6. Philosophy"],
    }
    units = textbook_units.get(grade, [f"Lesson {i}" for i in range(1, 16)])
    unit = st.selectbox("단원 선택", units)

col4, col5, col6 = st.columns(3)
with col4:
    num_questions = st.slider("문제 수", 10, 50, 30, step=5)
with col5:
    problem_type = st.multiselect("문제 유형", ["빈칸 채우기", "어법 판단", "순서 배열", "문장 완성", "오류 고치기", "어휘 선택"], default=["빈칸 채우기", "어법 판단"])
with col6:
    difficulty = st.radio("난이도", ["쉬움", "보통", "어려움"])

if st.button("PDF 문제지 + 해답지 생성하기", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 PDF 만드는 중..."):
        prompt = f"""
        엠베스트 SE 광사드림 학원 전용 문제지
        {grade} / {publisher} / {unit} / 난이도: {difficulty}
        {num_questions}문항 만들어줘. 유형은 {', '.join(problem_type)} 골고루.
        출력 형식:

        ===문제지===
        1. 문제 내용
            (a)  (b)  (c)  (d)

        ===해답지===
        1. 정답: (b)  해설: ...
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        parts = raw.split("===해답지===")
        worksheet = parts[0].replace("===문제지===", "").strip()
        answerkey = parts[1].strip() if len(parts) > 1 else ""

        # PDF 생성 함수
        def create_pdf(title, content):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Korean', fontName='Helvetica', fontSize=11, leading=14))
            story = []

            # 제목
            story.append(Paragraph(f"<font size=16><b>{title}</b></font>", styles["Title"]))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>{grade} {unit} 문법·독해 문제 ({num_questions}문항)</b>", styles["Korean"]))
            story.append(Spacer(1, 20))

            # 내용 라인별로
            for line in content.split('\n'):
                if line.strip():
                    story.append(Paragraph(line.strip(), styles["Korean"]))
                    story.append(Spacer(1, 6))

            doc.build(story)
            buffer.seek(0)
            return buffer

        # PDF 생성
        worksheet_pdf = create_pdf("엠베스트 SE 광사드림 학원 - 문제지", worksheet)
        answerkey_pdf = create_pdf("엠베스트 SE 광사드림 학원 - 해답지", answerkey)

        st.success("완성! 바로 인쇄하세요")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF 다운로드", worksheet_pdf, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF 다운로드", answerkey_pdf, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.balloons()

st.caption("© 2025 엠베스트 SE 광사드림 학원 전용 AI 문제 생성기")
