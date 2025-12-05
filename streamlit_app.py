import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO

# 페이지 설정
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 타이틀
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
    publisher = st.selectbox("교재", ["양주덕 (혁고등학교)", "옥빛"])

# 정확한 8과 단원명 (2023~2025년 실제 교과서 기준)
units_dict = {
    "중1": {
        "동아 (윤정미)": ["1. Nice to Meet You", "2. How Are You?", "3. My Day", "4. My Family",
                         "5. At School", "6. Let's Eat!", "7. My Favorite Things", "8. Seasons and Weather"]
    },
    "중2": {
        "천재 (정사열)": ["1. Suit Your Taste!", "2. Half a World Away", "3. I Wonder Why", "4. The Art of Living",
                         "5. Explore Your Feelings", "6. Doors to the Wild", "7. Art Around Us", "8. Changes Ahead"],
        "천재 (이재영)": ["1. Off to a Good Start", "2. My Life", "3. The World Around Me", "4. Let's Make a Difference",
                         "5. Dreams and Goals", "6. Science and Technology", "7. Culture and Heritage", "8. Viva South America!"],
        "비상 (김진완)": ["1. Getting to Know You", "2. What Do You Like?", "3. My Favorite Things", "4. Let's Go Shopping",
                         "5. Explore Your Feelings", "6. Doors to the Wild", "7. Art Around Us", "8. Changes Ahead"]
    },
    "중3": {
        "기본": ["1. Express Your Feelings", "2. Let's Make Our Town Better", "3. Heroes Around Us", "4. Let's Travel",
                 "5. Science and Us", "6. Korean Culture", "7. Global Issues", "8. Peace and Cooperation"]
    },
    "고1": {
        "양주덕 (혁고등학교)": ["1. Relationships", "2. Health", "3. Technology", "4. Environment", "5. Success", "6. Culture", "7. Economy", "8. Future"],
        "옥빛": ["1. People", "2. Lifestyle", "3. Technology", "4. Environment", "5. Success", "6. Culture", "7. Economy", "8. Global Issues"]
    },
    "고2": {
        "양주덕 (혁고등학교)": ["1. Decisions", "2. Leisure", "3. Global Issues", "4. Values", "5. Media", "6. Challenges", "7. Art", "8. History"],
        "옥빛": ["1. Choices", "2. Hobbies", "3. Global Problems", "4. Beliefs", "5. Information", "6. Life Challenges", "7. Arts", "8. Culture"]
    },
    "고3": {
        "양주덕 (혁고등학교)": ["1. Economy", "2. Ethics", "3. Literature", "4. History", "5. Science", "6. Philosophy", "7. Society", "8. Future"],
        "옥빛": ["1. Economy", "2. Ethics", "3. Art", "4. History", "5. Literature", "6. Philosophy", "7. Society", "8. Global Citizenship"]
    }
}

# 단원 선택 (출판사에 따라 정확한 8과)
units = units_dict.get(grade, {}).get(publisher, ["Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Unit 6", "Unit 7", "Unit 8"])
unit = st.selectbox("단원 선택", units)

# 옵션
col1, col2 = st.columns(2)
with col1:
    num_questions = st.slider("문제 수", 10, 50, 30, step=5)
with col2:
    difficulty = st.radio("난이도", ["쉬움", "보통", "어려움", "수능형"])

# 생성 버튼
if st.button("PDF 문제지 + 해답지 생성", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 문제지 만드는 중..."):
        prompt = f"""
        엠베스트 SE 광사드림 학원 전용 문제지
        {grade} {publisher} 교과서 {unit} 단원
        난이도: {difficulty}, 총 {num_questions}문항
        학교 시험지처럼 위아래 여백 넉넉하고 보기 ①②③④ 정렬 깔끔하게 만들어줘.
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

        # PDF 생성 (스타일 중복 문제 완전 해결!)
        def make_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=3.5 * cm, bottomMargin=3 * cm,
                                    leftMargin=2.5 * cm, rightMargin=2.5 * cm)
            styles = getSampleStyleSheet()

            # 중복 없이 새 스타일 정의
            body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=12, leading=24, spaceAfter=20)
            title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, alignment=1, spaceAfter=30)

            story = [
                Paragraph("엠베스트 SE 광사드림 학원", title_style),
                Paragraph(title, title_style),
                Spacer(1, 40)
            ]

            for line in content.split("\n"):
                if line.strip():
                    if is_answer:
                        story.append(Paragraph(f"<font color='red'><b>{line.strip()}</b></font>", body_style))
                    else:
                        story.append(Paragraph(line.strip(), body_style))
                    story.append(Spacer(1, 25))

            doc.build(story)
            buffer.seek(0)
            return buffer

        ws = make_pdf(f"{grade} {unit} 문법·독해 문제 ({num_questions}문항)", worksheet)
        ak = make_pdf(f"{grade} {unit} 정답 및 해설", answerkey, is_answer=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF 다운로드", ws, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF 다운로드", ak, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.success("완성! 학원에서 바로 인쇄 가능")
        st.balloons()

st.caption("© 2025 엠베스트 SE 광사드림 학원 전용 AI 문제 생성기")
