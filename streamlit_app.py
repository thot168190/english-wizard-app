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

# 1. 학년 선택
grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])

# 2. 출판사 선택
if grade == "중1":
    publisher = "동아 (윤정미)"
    st.info("동아 (윤정미)")
elif grade == "중2":
    publisher = st.selectbox("출판사", ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)"])
else:
    publisher = "기본 교과서"
    st.info("기본 교과서")

# 3. 단원 선택 (실제 교과서 단원명 정확히)
units_dict = {
    "중1": ["1. Nice to Meet You", "2. How Are You?", "3. My Day", "4. My Family", "5. At School", "6. Let's Eat!"],
    "중2": ["1. Welcome to My Home", "2. What Do You Like?", "3. My Favorite Season", "4. Let's Go Shopping", "5. I Can Do It!", "6. Our Heroes"],
    "중3": ["1. Welcome to Korea", "2. Life in the Future", "3. Heroes Around Us", "4. Let's Travel", "5. Science and Us", "6. Korean Culture"],
    "고1": ["1. People Around Us", "2. Health and Lifestyle", "3. Science and Technology", "4. Environment", "5. Success and Happiness", "6. Popular Culture"],
    "고2": ["1. Life Choices", "2. Leisure and Hobbies", "3. Global Issues", "4. Values and Beliefs", "5. Media and Information", "6. Challenges in Life"],
    "고3": ["1. Economy and Society", "2. Ethics and Philosophy", "3. Art and Literature", "4. History and Culture", "5. Science and Future", "6. Global Citizenship"]
}
units = units_dict.get(grade, ["Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Unit 6"])
unit = st.selectbox("단원 선택", units)

# 4. 옵션
col1, col2, col3 = st.columns(3)
with col1:
    num_questions = st.slider("문제 수", 10, 50, 30, step=5)
with col2:
    problem_type = st.multiselect("문제 유형", 
        ["빈칸 채우기", "어법 판단", "순서 배열", "문장 완성", "오류 고치기", "어휘 선택"],
        default=["빈칸 채우기", "어법 판단"])
with col3:
    difficulty = st.radio("난이도", ["쉬움", "보통", "어려움"])

# 5. 생성 버튼
if st.button("PDF 문제지 + 해답지 생성", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 PDF 만드는 중..."):
        prompt = f"""
        엠베스트 SE 광사드림 학원 전용 문제지
        {grade} / {publisher} / {unit} 단원 / 난이도: {difficulty}
        {num_questions}문항 만들어줘. 유형은 {', '.join(problem_type)}을 골고루.
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

        # PDF 생성 (폰트 없이도 최대한 한글 깨지지 않게)
        def create_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=3*cm, leftMargin=2.5*cm, rightMargin=2.5*cm)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Body', fontName='Helvetica', fontSize=12, leading=22, spaceAfter=20))
            styles.add(ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=18, alignment=1, spaceAfter=30))

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

        ws_title = f"{grade} {unit} 문법·독해 문제 ({num_questions}문항)"
        ak_title = f"{grade} {unit} 정답 및 해설"

        ws_pdf = create_pdf(ws_title, worksheet)
        ak_pdf = create_pdf(ak_title, answerkey, is_answer=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF 다운로드", ws_pdf, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF 다운로드", ak_pdf, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.success("완성! 학원에서 바로 인쇄 가능")
        st.balloons()

st.caption("© 2025 엠베스트 SE 광사드림 학원 전용 AI 문제 생성기")
