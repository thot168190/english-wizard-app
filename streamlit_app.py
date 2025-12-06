import streamlit as st
import google.generativeai as genai
from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# 폰트 등록 (fonts 폴더에 파일이 있어야 함)
# 만약 파일명이 다르면 실제 파일명으로 수정해주세요.
pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Google API Key가 설정되지 않았습니다.")

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>AI 실전 모의고사 생성기 (2단 편집 Ver)</h3>", unsafe_allow_html=True)
st.markdown("---")

# --- 입력 옵션 ---
col1, col2, col3 = st.columns(3)
with col1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
with col2:
    if "중" in grade:
        publisher = st.selectbox("출판사", ["동아 (윤정미)", "천재 (정사열)", "천재 (이재영)", "비상 (김진완)", "미래엔 (최연희)"])
    else:
        publisher = "수능특강/모의고사"
        st.info("고등부는 모의고사 형식으로 생성됩니다.")
with col3:
    unit = st.text_input("단원명 (예: 1. Nice to Meet You)", "1. Nice to Meet You")

num_questions = st.slider("문항 수", 10, 40, 20, step=5)

# --- PDF 생성 함수 (핵심 수정 부분) ---
def create_2column_pdf(doc_title, header_info, content_text):
    buffer = BytesIO()
    
    # 1. 문서 템플릿 설정 (여백 조정)
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=15*mm, bottomMargin=15*mm)

    # 2. 스타일 정의
    styles = getSampleStyleSheet()
    # 문제 본문 스타일
    style_body = ParagraphStyle(
        name='ExamBody',
        parent=styles['Normal'],
        fontName='NotoSansKR',
        fontSize=10.5,
        leading=16, # 줄간격
        spaceAfter=12, # 문단 뒤 여백
        alignment=0 # 좌정렬
    )
    # 제목 스타일 (큰 제목이 필요할 경우)
    style_title = ParagraphStyle(
        name='ExamTitle',
        parent=styles['Heading1'],
        fontName='NotoSansKR',
        fontSize=14,
        alignment=1,
        spaceAfter=20
    )

    # 3. 2단 레이아웃 프레임 정의
    # A4 너비: 210mm, 높이: 297mm
    # 좌우 여백 10mm 제외하면 가용 너비 190mm -> 단 너비 약 90mm, 간격 10mm
    
    frame_w = 90*mm
    frame_h = 240*mm # 헤더/푸터 제외한 높이
    gap = 10*mm
    
    # 1페이지용 프레임 (헤더 때문에 시작 위치가 조금 낮음)
    frame_first_left = Frame(10*mm, 20*mm, frame_w, 220*mm, id='F1_L')
    frame_first_right = Frame(10*mm + frame_w + gap, 20*mm, frame_w, 220*mm, id='F1_R')
    
    # 2페이지부터 쓸 프레임 (전체 높이 활용)
    frame_later_left = Frame(10*mm, 20*mm, frame_w, 255*mm, id='F2_L')
    frame_later_right = Frame(10*mm + frame_w + gap, 20*mm, frame_w, 255*mm, id='F2_R')

    # 4. 페이지 템플릿 정의 (그리기 함수 연결)
    def draw_first_page(canvas, doc):
        canvas.saveState()
        
        # [헤더 박스 그리기]
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.5)
        
        # 큰 테두리 대신 상단 제목 영역
        canvas.setFont("NotoSansKR", 20)
        canvas.drawCentredString(A4[0]/2, 275*mm, header_info['title']) # 메인 타이틀
        
        canvas.setFont("NotoSansKR", 12)
        canvas.drawCentredString(A4[0]/2, 265*mm, header_info['sub_title']) # 서브 타이틀
        
        # 결재란/정보란 박스 (오른쪽 상단)
        # 학년, 반, 번호, 이름 박스
        box_y = 250*mm
        canvas.setFont("NotoSansKR", 10)
        
        # 선 그리기
        canvas.line(10*mm, box_y, 200*mm, box_y) # 위쪽 선
        canvas.line(10*mm, box_y - 10*mm, 200*mm, box_y - 10*mm) # 아래쪽 선 (박스 끝)
        
        # 텍스트 배치 (간격 띄워서)
        info_text = f"제 {header_info['grade']} 학년      반      번    이름 : ____________________    점수 : __________"
        canvas.drawString(15*mm, box_y - 7*mm, info_text)
        
        # [단 구분선] - 중앙 점선
        canvas.setDash(2, 2) # 점선 설정
        canvas.line(A4[0]/2, 20*mm, A4[0]/2, 240*mm)
        
        # [푸터]
        canvas.restoreState() # 상태 복구 (실선으로 돌아옴)
        canvas.setFont("NotoSansKR", 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {doc.page} -")
        canvas.drawString(10*mm, 10*mm, "엠베스트 SE 광사드림 학원")

    def draw_later_page(canvas, doc):
        canvas.saveState()
        # [단 구분선]
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 20*mm, A4[0]/2, 280*mm)
        
        # [푸터]
        canvas.restoreState()
        canvas.setFont("NotoSansKR", 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {doc.page} -")
        canvas.drawString(10*mm, 10*mm, "엠베스트 SE 광사드림 학원")

    template_first = PageTemplate(id='First', frames=[frame_first_left, frame_first_right], onPage=draw_first_page)
    template_later = PageTemplate(id='Later', frames=[frame_later_left, frame_later_right], onPage=draw_later_page)

    doc.addPageTemplates([template_first, template_later])

    # 5. 내용 채우기 (Story)
    story = []
    
    # 문제 텍스트 줄바꿈 처리해서 넣기
    for line in content_text.split('\n'):
        if line.strip():
            # 문제 번호가 있는 줄은 약간 더 굵게 하거나 공백 추가 가능
            text = line.strip()
            # 간단한 파싱: 문항 번호로 시작하면 줄바꿈 추가
            # if text[0].isdigit() and "." in text[:3]:
            #     story.append(Spacer(1, 5*mm))
            
            p = Paragraph(text, style_body)
            story.append(p)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- 메인 실행 로직 ---
if st.button("2단형 실전 시험지 생성", type="primary", use_container_width=True):
    with st.spinner("AI가 문제를 출제하고 레이아웃을 잡는 중입니다..."):
        # 프롬프트 구성
        prompt = f"""
        엠베스트 SE 광사드림 학원 영어 시험지 출제.
        대상: {grade}
        교과서: {publisher}
        단원: {unit}
        문항수: {num_questions}
        난이도: 중상
        
        [출력 형식 가이드]
        - 문제지 부분과 정답지 부분을 명확히 구분해줘.
        - 객관식 보기는 ①, ②, ③, ④, ⑤ 특수문자를 사용해.
        - 지문이 필요한 문제는 [지문] 내용을 포함해줘.
        - 각 문제는 "1. 다음 중..." 형식으로 번호를 매겨줘.
        
        형식:
        ===문제지===
        (문제들...)
        ===정답지===
        (정답 및 해설...)
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash") # 최신 안정화 모델 사용 권장
        response = model.generate_content(prompt)
        text_data = response.text
        
        # 문제지 / 정답지 분리
        if "===정답지===" in text_data:
            parts = text_data.split("===정답지===")
            q_text = parts[0].replace("===문제지===", "").strip()
            a_text = parts[1].strip()
        else:
            q_text = text_data
            a_text = "정답지가 생성되지 않았습니다."

        # PDF 헤더 정보
        header_info_q = {
            'title': f"{unit} 단원평가",
            'sub_title': f"[{publisher}] {grade} 1학기 중간/기말 대비",
            'grade': grade.replace("중","").replace("고","")
        }
        
        header_info_a = {
            'title': "정답
