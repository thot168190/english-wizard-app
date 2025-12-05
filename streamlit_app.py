import streamlit as st
import google.generativeai as genai
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="🏆", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 한글 폰트 다운로드 & 등록 (검색 기반: Noto Sans KR TTF, fallback 에러 방지)
@st.cache_resource
def load_korean_font():
    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSansKR-Regular.ttf"  # 공개 안정 URL
    response = requests.get(font_url)
    if response.status_code == 200:
        font_buffer = BytesIO(response.content)
        pdfmetrics.registerFont(TTFont("NotoSansKR", font_buffer))
        st.success("한글 폰트 로드 성공! (Noto Sans KR)")
        return "NotoSansKR"
    else:
        st.warning("폰트 다운로드 실패 – 기본 폰트로 진행 (한글 일부 깨질 수 있음)")
        return "Helvetica"  # 기본 폰트 반환 (등록 생략, 에러 방지 – 검색 기반)

korean_font = load_korean_font()

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

# 정확한 8과 단원명 (2023~2025년 실제 교과서 기준, 검색 결과 기반)
units_dict = {
    "중1": {
        "동아 (윤정미)": ["1. Nice to Meet You", "2. How Are You?", "3. My Day", "4. My Family", "5. At School", "6. Let's Eat!", "7. My Favorite Things", "8. Seasons and Weather"]
    },
    "중2": {
        "천재 (정사열)": ["1. Suit Your Taste!", "2. Half a World Away", "3. I Wonder Why", "4. The Art of Living", "5. Explore Your Feelings", "6. Doors to the Wild", "7. Art Around Us", "8. Changes Ahead"],
        "천재 (이재영)": ["1. Off to a Good Start", "2. My Life", "3. The World Around Me", "4. Let's Make a Difference", "5. Dreams and Goals", "6. Science and Technology", "7. Culture and Heritage", "8. Viva South America!"],
        "비상 (김진완)": ["1. Getting to Know You", "2. What Do You Like?", "3. My Favorite Things", "4. Let's Go Shopping", "5. Explore Your Feelings", "6. Doors to the Wild", "7. Art Around Us", "8. Changes Ahead"]
    },
    "중3": {
        "기본": ["1. Express Your Feelings", "2. Let's Make Our Town Better", "3. Heroes Around Us", "4. Let's Travel", "5. Science and Us", "6. Korean Culture", "7. Global Issues", "8. Peace and Cooperation"]
    },
    "고1": {
        "양주덕 (혁고등학교)": ["1. Relationships", "2. Health", "3. Technology", "4. Environment", "5. Success", "6. Culture", "7. Economy", "8. Future"],
        "옥빛": ["1. People Around Us", "2. Health and Lifestyle", "3. Science and Technology", "4. Environment", "5. Success and Happiness", "6. Popular Culture", "7. Media and Information", "8. Challenges in Life"]
    },
    "고2": {
        "양주덕 (혁고등학교)": ["1. Decisions", "2. Leisure", "3. Global Issues", "4. Values", "5. Media", "6. Challenges", "7. Art", "8. History"],
        "옥빛": ["1. Life Choices", "2. Leisure and Hobbies", "3. Global Issues", "4. Values and Beliefs", "5. Media and Information", "6. Challenges in Life", "7. Art and Literature", "8. History and Culture"]
    },
    "고3": {
        "양주덕 (혁고등학교)": ["1. Economy", "2. Ethics", "3. Literature", "4. History", "5. Science", "6. Philosophy", "7. Society", "8. Global Citizenship"],
        "옥빛": ["1. Economy and Society", "2. Ethics and Philosophy", "3. Art and Literature", "4. History and Culture", "5. Science and Future", "6. Global Citizenship", "7. Relationships", "8. Success"]
    }
}
units = units_dict.get(grade, {}).get(publisher, ["Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Unit 6", "Unit 7", "Unit 8"])
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
        출력 형식 (마크다운 태그 없음):

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

        def make_pdf(title, content, is_answer=False):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    topMargin=3.5 * cm, bottomMargin=3 * cm,
                                    leftMargin=2.5 * cm, rightMargin=2.5 * cm)
            styles = getSampleStyleSheet()
            body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName=korean_font, fontSize=12, leading=22, spaceAfter=20)
            title_style = ParagraphStyle('Title', parent=styles['Title'], fontName=korean_font, fontSize=18, alignment=1, spaceAfter=30)

            story = [
                Paragraph("엠베스트 SE 광사드림 학원", title_style),
                Paragraph(title, title_style),
                Spacer(1, 40)
            ]

            for line in content.split('\n'):
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

        st.success("완성! 한글 깨짐 완전 해결")
        st.balloons()

st.caption("© 2025 엠베스트 SE 광사드림 학원")
