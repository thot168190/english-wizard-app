import streamlit as st
import google.generativeai as genai
from reportlab.platypus import BaseDocTemplate, Paragraph, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# --------------------------------------------------------------------------
# 1. 초기 설정 및 폰트 등록
# --------------------------------------------------------------------------
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")

# [중요] 폰트 파일 체크
try:
    pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))
except:
    st.error("⚠️ 폰트 로드 실패: 'fonts' 폴더에 'NotoSansKR-Regular.ttf' 파일이 있는지 확인해주세요.")

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Google API Key가 설정되지 않았습니다. secrets.toml 파일을 확인해주세요.")

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
        publisher = st.selectbox("출판사", ["동아 (윤정미)", "천재 (정사열)", "천재 (이재영)", "비상 (김진완)", "미래엔 (최연희)"])
    else:
        publisher = "수능특강/모의고사 변형"
with col3:
    unit = st.text_input("단원명 (예: 1. Nice to Meet You)", "1. Nice to Meet You")

# 문제 수 및 난이도 조절
c1, c2 = st.columns(2)
with c1:
    num_questions = st.slider("문항 수", 10, 30, 20, step=5)
with c2:
    difficulty = st.select_slider("난이도 설정", options=["하", "중", "상", "최상"], value="상")

# --------------------------------------------------------------------------
# 3. PDF 생성 로직 (2단 레이아웃 + 시험지 헤더)
# --------------------------------------------------------------------------
def create_2column_pdf(doc_title, header_info, content_text):
    buffer = BytesIO()
    
    # 문서 여백 설정
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    
    # 본문 스타일
    style_body = ParagraphStyle(
        name='ExamBody',
        parent=styles['Normal'],
        fontName='NotoSansKR',
        fontSize=10.5,
        leading=17,       # 줄 간격
        spaceAfter=12,    # 문단 뒤 간격
        alignment=0       # 좌정렬
    )

    # 2단 프레임 설정
    frame_w = 90*mm   # 한 단의 너비
    gap = 10*mm       # 단 사이 간격
    
    frame_h_first = 220*mm # 1페이지 높이
    frame_h_later = 255*mm # 2페이지 이후 높이

    # 프레임 정의
    frame_first_left = Frame(10*mm, 20*mm, frame_w, frame_h_first, id='F1_L')
    frame_first_right = Frame(10*mm + frame_w + gap, 20*mm, frame_w, frame_h_first, id='F1_R')
    
    frame_later_left = Frame(10*mm, 20*mm, frame_w, frame_h_later, id='F2_L')
    frame_later_right = Frame(10*mm + frame_w + gap, 20*mm, frame_w, frame_h_later, id='F2_R')

    # [1페이지 그리기 함수]
    def draw_first_page(canvas, doc):
        canvas.saveState()
        
        # 1. 메인 타이틀
        canvas.setFont("NotoSansKR", 20)
        canvas.drawCentredString(A4[0]/2, 275*mm, header_info['title']) 
        
        # 2. 서브 타이틀
        canvas.setFont("NotoSansKR", 12)
        canvas.drawCentredString(A4[0]/2, 265*mm, header_info['sub_title']) 
        
        # 3. 결재란 (우측 상단)
        box_y = 250*mm
        canvas.setFont("NotoSansKR", 10)
        canvas.setLineWidth(0.5)
        
        canvas.line(10*mm, box_y, 200*mm, box_y) 
        canvas.line(10*mm, box_y - 10*mm, 200*mm, box_y - 10*mm)
        
        info_text = f"제 {header_info['grade']} 학년      반      번    이름 : ____________________    점수 : __________"
        canvas.drawString(15*mm, box_y - 7*mm, info_text)
        
        # 4. 단 구분선 (중앙 점선)
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 20*mm, A4[0]/2, 240*mm)
        
        # 5. 하단 푸터
        canvas.restoreState()
        canvas.setFont("NotoSansKR", 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {doc.page} -")
        canvas.drawString(10*mm, 10*mm, "엠베스트 SE 광사드림 학원")

    # [2페이지 이후 그리기 함수]
    def draw_later_page(canvas, doc):
        canvas.saveState()
        # 중앙 점선
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 20*mm, A4[0]/2, 280*mm)
        
        canvas.restoreState()
        canvas.setFont("NotoSansKR", 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {doc.page} -")
        canvas.drawString(10*mm, 10*mm, "엠베스트 SE 광사드림 학원")

    # 템플릿 등록
    template_first = PageTemplate(id='First', frames=[frame_first_left, frame_first_right], onPage=draw_first_page)
    template_later = PageTemplate(id='Later', frames=[frame_later_left, frame_later_right], onPage=draw_later_page)

    doc.addPageTemplates([template_first, template_later])

    # 내용 채우기
    story = []
    for line in content_text.split('\n'):
        if line.strip():
            p = Paragraph(line.strip(), style_body)
            story.append(p)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------
# 4. 메인 실행 및 AI 생성 로직
# --------------------------------------------------------------------------
if st.button("High-Level 실전 시험지 생성", type="primary", use_container_width=True):
    with st.spinner("AI가 문제를 출제하고 있습니다... (약 10~20초 소요)"):
        
        prompt = f"""
        당신은 엠베스트 SE 영어 강사입니다.
        아래 조건에 맞춰 완벽한 시험지를 작성하세요.
        
        [출제 정보]
        - 대상: {grade}
        - 범위: {publisher}, {unit}
        - 문항: {num_questions}문항
        - 난이도: {difficulty}

        [형식 가이드]
        1. 모든 문제는 '1.', '2.' 숫자로 시작.
        2. 보기: ①, ②, ③, ④, ⑤ 특수문자 사용.
        3. 지문 필요 시 [지문] 표시 후 내용 작성.
        4. 문제지와 정답지는 '===절취선==='으로 구분.
        5. 정답지는 '1. 정답: ① / 해설: ...' 형식.
        
        [작성 시작]
        ===문제지===
        """
        
        try:
            # [수정] 모델을 안정적인 1.5-flash로 변경 (404 에러 방지)
            model = genai.GenerativeModel("gemini-1.5-flash") 
            response = model.generate_content(prompt)
            text_data = response.text
            
            # 파싱
            if "===절취선===" in text_data:
                parts = text_data.split("===절취선===")
                q_text = parts[0].replace("===문제지===", "").strip()
                a_text = parts[1].replace("===정답지===", "").strip()
            else:
                q_text = text_data
                a_text = "⚠️ 정답지 구분선을 찾지 못했습니다. 전체 내용을 확인해주세요."

            # 헤더 정보
            grade_clean = grade.replace("중","").replace("고","")
            header_info_q = {
                'title': f"{unit} 단원평가",
                'sub_title': f"[{publisher}] {grade} 내신 대비",
                'grade': grade_clean
            }
            
            header_info_a = {
                'title': "정답 및 해설",
                'sub_title': f"{unit} 단원평가",
                'grade': "" 
            }

            # PDF 생성
            pdf_q = create_2column_pdf(f"{grade} 시험지", header_info_q, q_text)
            pdf_a = create_2column_pdf(f"{grade} 정답지", header_info_a, a_text)

            # 다운로드 버튼
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.success("✅ 문제지 생성 완료")
                st.download_button("📄 문제지 다운로드", pdf_q, f"엠베스트_{grade}_문제지.pdf", "application/pdf")
            with col_d2:
                st.success("✅ 정답지 생성 완료")
                st.download_button("🔑 정답지 다운로드", pdf_a, f"엠베스트_{grade}_해설지.pdf", "application/pdf")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# [수정] 저작권 안내 오른쪽 정렬
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: right; color: gray; font-size: 0.8em;'>
        Developed by 엠베스트 SE 광사드림 학원 (Powered by Gemini)
    </div>
    """, 
    unsafe_allow_html=True
)
