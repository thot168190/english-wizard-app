import streamlit as st
import google.generativeai as genai
from reportlab.platypus import BaseDocTemplate, Paragraph, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import requests

# --------------------------------------------------------------------------
# 1. 초기 설정 및 폰트 자동 설치
# --------------------------------------------------------------------------
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="🏆", layout="wide")

# [폰트 설정] 파일이 없으면 자동으로 다운로드
font_path = "NanumGothic.ttf"
if not os.path.exists(font_path):
    url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    try:
        response = requests.get(url)
        with open(font_path, "wb") as f:
            f.write(response.content)
    except:
        pass

# 폰트 등록
try:
    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
    base_font = "NanumGothic"
except:
    base_font = "Helvetica"

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --------------------------------------------------------------------------
# 2. UI 화면 구성
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>최고급 AI 실전 시험지 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

if "ws_pdf" not in st.session_state:
    st.session_state.ws_pdf = None
if "ak_pdf" not in st.session_state:
    st.session_state.ak_pdf = None

col1, col2, col3 = st.columns(3)
with col1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
with col2:
    unit = st.selectbox("단원", ["1. Lesson 1", "2. Lesson 2", "3. Lesson 3", "4. Special Lesson"])
with col3:
    num_questions = st.slider("문제 수", 10, 40, 30, step=5)

# --------------------------------------------------------------------------
# 3. 고급 PDF 생성 로직 (2단, 첫 페이지 헤더 분리, 우측 하단 정렬)
# --------------------------------------------------------------------------
def create_advanced_pdf(doc_title, header_info, content_text):
    buffer = BytesIO()
    
    # 전체 여백 설정
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    style_body = ParagraphStyle(
        name='ExamBody',
        parent=styles['Normal'],
        fontName=base_font,
        fontSize=10,
        leading=16,
        spaceAfter=10,
        alignment=0, # 왼쪽 정렬
        wordWrap='CJK'
    )

    # --- 프레임 설정 (2단 레이아웃) ---
    frame_w = 92*mm   # 1단 너비
    gap = 6*mm        # 단 간격
    
    # 1페이지용 높이 (헤더 공간 제외)
    frame_h_first = 230*mm 
    # 2페이지 이후용 높이 (풀 사이즈)
    frame_h_later = 260*mm 

    # 1페이지 프레임 (좌/우)
    frame_first_left = Frame(10*mm, 15*mm, frame_w, frame_h_first, id='F1_L')
    frame_first_right = Frame(10*mm + frame_w + gap, 15*mm, frame_w, frame_h_first, id='F1_R')
    
    # 2페이지 프레임 (좌/우)
    frame_later_left = Frame(10*mm, 15*mm, frame_w, frame_h_later, id='F2_L')
    frame_later_right = Frame(10*mm + frame_w + gap, 15*mm, frame_w, frame_h_later, id='F2_R')

    # --- 그리기 함수 ---
    
    # [첫 페이지 디자인] : 헤더 있음
    def draw_first_page(canvas, doc):
        canvas.saveState()
        
        # 1. 메인 타이틀
        canvas.setFont(base_font, 18)
        canvas.drawCentredString(A4[0]/2, 280*mm, header_info['title']) 
        
        # 2. 서브 타이틀
        canvas.setFont(base_font, 11)
        canvas.drawCentredString(A4[0]/2, 272*mm, header_info['sub_title']) 
        
        # 3. 결재란/정보 박스
        box_y = 260*mm
        canvas.setFont(base_font, 10)
        canvas.setLineWidth(0.5)
        canvas.line(10*mm, box_y, 200*mm, box_y) 
        canvas.line(10*mm, box_y - 8*mm, 200*mm, box_y - 8*mm)
        
        info_text = f"제 {header_info['grade']} 학년      반      번     이름 : ____________________     점수 : __________"
        canvas.drawString(15*mm, box_y - 6*mm, info_text)
        
        # 4. 중앙 구분선
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 250*mm)
        
        # 5. 하단 푸터 (우측 하단 정렬)
        canvas.restoreState()
        canvas.setFont(base_font, 9)
        canvas.drawCentredString(A4[0]/2, 7*mm, f"- {doc.page} -")
        # [요청사항] 학원명 오른쪽 정렬
        canvas.drawRightString(200*mm, 7*mm, "엠베스트 SE 광사드림 학원")

    # [두 번째 페이지부터 디자인] : 헤더 없음
    def draw_later_page(canvas, doc):
        canvas.saveState()
        # 중앙 구분선
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 285*mm)
        
        canvas.restoreState()
        canvas.setFont(base_font, 9)
        canvas.drawCentredString(A4[0]/2, 7*mm, f"- {doc.page} -")
        # [요청사항] 학원명 오른쪽 정렬
        canvas.drawRightString(200*mm, 7*mm, "엠베스트 SE 광사드림 학원")

    # 템플릿 등록
    template_first = PageTemplate(id='First', frames=[frame_first_left, frame_first_right], onPage=draw_first_page)
    template_later = PageTemplate(id='Later', frames=[frame_later_left, frame_later_right], onPage=draw_later_page)

    doc.addPageTemplates([template_first, template_later])

    # 내용 채우기
    story = []
    for line in content_text.split('\n'):
        if line.strip():
            clean_line = line.strip().replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(clean_line, style_body))
            
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF 생성 오류: {e}")
        return None

# --------------------------------------------------------------------------
# 4. 메인 실행
# --------------------------------------------------------------------------
if st.button("최고급 실전 시험지 생성 (완전 완벽)", type="primary", use_container_width=True):
    with st.spinner("최고급 시험지 생성 중..."):
        
        prompt = f"""
        엠베스트 SE 광사드림 학원 실전 시험지
        {grade} {unit} 단원, 총 {num_questions}문항
        최고 퀄리티로 만들어줘.

        [출력 형식]
        ===문제지===
        1. 문제 내용...
           ① ... ② ...
        
        ===해답지===
        1. 정답 및 해설...
        """
        
        try:
            # [요청사항] 사용자가 입력한 모델명 그대로 유지
            model = genai.GenerativeModel("gemini-2.5-flash") 
            response = model.generate_content(prompt)
            raw = response.text

            # 파싱
            worksheet_text = ""
            answerkey_text = ""
            
            if "===해답지===" in raw:
                parts = raw.split("===해답지===")
                worksheet_text = parts[0].replace("===문제지===", "").strip()
                answerkey_text = parts[1].strip()
            else:
                worksheet_text = raw
                answerkey_text = "해답지 구분선을 찾지 못했습니다."

            # 헤더 정보
            header_ws = {'title': f"{unit} 실전 평가", 'sub_title': f"{grade} 내신 완벽 대비", 'grade': grade}
            header_ak = {'title': "정답 및 해설", 'sub_title': f"{unit} 확인 학습", 'grade': grade}

            # PDF 생성 (고급 모드)
            st.session_state.ws_pdf = create_advanced_pdf(f"{grade} 시험지", header_ws, worksheet_text)
            st.session_state.ak_pdf = create_advanced_pdf(f"{grade} 정답지", header_ak, answerkey_text)

            st.session_state.generated = True

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# 다운로드 버튼
if st.session_state.ws_pdf:
    c1, c2 = st.columns(2)
    with c1:
        st.success("문제지 생성 완료")
        st.download_button("📄 문제지 PDF", st.session_state.ws_pdf, f"엠베스트_{grade}_문제.pdf", "application/pdf")
    with c2:
        st.success("정답지 생성 완료")
        st.download_button("🔑 정답지 PDF", st.session_state.ak_pdf, f"엠베스트_{grade}_정답.pdf", "application/pdf")

st.caption("© 2025 엠베스트 SE 광사드림 학원")
