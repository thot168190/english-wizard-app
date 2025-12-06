import streamlit as st
import google.generativeai as genai
from reportlab.platypus import BaseDocTemplate, Paragraph, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# --------------------------------------------------------------------------
# 1. 초기 설정 및 폰트 등록
# --------------------------------------------------------------------------
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")

# [폰트 설정]
try:
    pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))
    base_font = "NotoSansKR"
except:
    base_font = "Helvetica" # 폰트가 없으면 영문 기본 폰트 사용

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Google API Key가 설정되지 않았습니다. secrets.toml 파일을 확인해주세요.")
    st.stop()

# --------------------------------------------------------------------------
# 2. UI 화면 구성
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>High-Level AI 실전 모의고사 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# 상단 선택 옵션
col1, col2, col3 = st.columns(3)

with col1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])

with col2:
    if "중" in grade:
        publisher_list = ["동아 (윤정미)", "천재 (정사열)", "천재 (이재영)", "비상 (김진완)", "미래엔 (최연희)", "기타"]
    elif grade == "고2":
        publisher_list = ["YBM (박준언)", "YBM (한상호)", "천재 (이재영)", "비상 (홍민표)", "수능특강", "모의고사"]
    else:
        publisher_list = ["수능특강", "모의고사", "교과서 공통"]
    publisher = st.selectbox("출판사/범위", publisher_list)

with col3:
    unit = st.text_input("단원명 (예: 1. Lesson 1)", "1. The Part You Play")

# 문제 수 및 난이도 조절
c1, c2 = st.columns(2)
with c1:
    num_questions = st.slider("문항 수", 10, 30, 20, step=5)
with c2:
    difficulty = st.select_slider("난이도 설정", options=["하", "중", "상", "최상"], value="상")

# --------------------------------------------------------------------------
# 3. PDF 생성 로직 (2단 레이아웃 + 시험지 헤더 복구)
# --------------------------------------------------------------------------
def create_2column_pdf(doc_title, header_info, content_text):
    buffer = BytesIO()
    
    # 여백 설정 (시험지처럼)
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    
    # 본문 스타일 (가독성 최적화)
    style_body = ParagraphStyle(
        name='ExamBody',
        parent=styles['Normal'],
        fontName=base_font,
        fontSize=10.5,
        leading=17,       # 줄 간격
        spaceAfter=12,    # 문단 뒤 간격
        alignment=0       # 좌정렬
    )

    # 2단 프레임 설정
    frame_w = 90*mm   # 한 단의 너비
    gap = 10*mm       # 단 사이 간격
    
    frame_h_first = 220*mm # 1페이지 높이 (헤더 공간 제외)
    frame_h_later = 255*mm # 2페이지 이후 높이

    # 프레임 정의
    frame_first_left = Frame(10*mm, 20*mm, frame_w, frame_h_first, id='F1_L')
    frame_first_right = Frame(10*mm + frame_w + gap, 20*mm, frame_w, frame_h_first,
