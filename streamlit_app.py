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

# [폰트 설정] fonts 폴더 체크
try:
    pdfmetrics.registerFont(TTFont("NotoSansKR", "fonts/NotoSansKR-Regular.ttf"))
    base_font = "NotoSansKR"
except:
    base_font = "Helvetica" # 폰트 파일 없으면 영문 기본 폰트 사용

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Google API Key가 설정되지 않았습니다. secrets.toml 파일을 확인해주세요.")
    st.stop()

# --------------------------------------------------------------------------
# 2. UI 화면 구성
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>High-Level AI 실전 모의고사 생성기</h3>", unsafe_allow_html=True)
st.markdown("---")

# [핵심 수정] 사용 가능한 AI 모델 자동 감지 및 선택 기능
st.sidebar.header("🔧 AI 모델 설정")
try:
    # API 키로 접근 가능한 모든 모델 리스트 가져오기
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    
    # 모델이 하나도 안 뜰 경우 대비
    if not available_models:
        st.sidebar.error("사용 가능한 모델을 찾을 수 없습니다. API 키 권한을 확인해주세요.")
        selected_model_name = "models/gemini-pro" # 강제 기본값
    else:
        # 사용자가 직접 선택하도록 함 (가장 최신 모델을 기본값으로)
        selected_model_name = st.sidebar.selectbox(
            "사용할 AI 모델 선택 (에러 시 변경해보세요)", 
            available_models, 
            index=0
        )
        st.sidebar.success(f"선택됨: {selected_model_name}")

except Exception as e:
    st.sidebar.error(f"모델 목록을 가져오는데 실패했습니다: {e}")
    selected_model_name = "models/gemini-pro"

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
# 3. PDF 생성 로직 (2단 레이아웃 + 시험지 헤더)
# --------------------------------------------------------------------------
def create_2column_pdf(doc_title, header_info, content_text):
    buffer = BytesIO()
    
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    
    style_body = ParagraphStyle(
        name='ExamBody',
        parent=styles['Normal'],
        fontName=base_font,
        fontSize=10.5,
        leading=17,
        spaceAfter=12,
        alignment=0
    )

    frame_w = 90*mm
    gap = 10*mm
    
    frame_h_first = 220*mm 
    frame_h_later = 255*mm 

    frame_first_left = Frame(10*mm, 20*mm, frame_w, frame_h_first, id='F1_L')
    frame_first_right = Frame(10*mm + frame_w + gap, 20*mm, frame_w, frame_h_first, id='F1_R')
    
    frame_later_left = Frame(10*mm, 20*mm, frame_w, frame_h_later, id='F2_L')
    frame_later_right = Frame(10*mm + frame_w + gap, 20*mm, frame_w, frame_h_later, id='F2_R')

    def draw_first_page(canvas, doc):
        canvas.saveState()
        canvas.setFont(base_font, 20)
        canvas.drawCentredString(A4[0]/2, 275*mm, header_info['title']) 
        canvas.setFont(base_font, 12)
        canvas.drawCentredString(A4[0]/2, 265*mm, header_info['sub_title']) 
        
        box_y = 250*mm
        canvas.setFont(base_font, 10)
        canvas.setLineWidth(0.5)
        canvas.line(10*mm, box_y, 200*mm, box_y) 
        canvas.line(10*mm, box_y - 10*mm, 200*mm, box_y - 10*mm)
        info_text = f"제 {header_info['grade']} 학년      반      번    이름 : ____________________    점수 : __________"
        canvas.drawString(15*mm, box_y - 7*mm, info_text)
        
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 20*mm, A4[0]/2, 240*mm)
        
        canvas.restoreState()
        canvas.setFont(base_font, 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {doc.page} -")
        canvas.drawString(10*mm, 10*mm, "엠베스트 SE 광사드림 학원")

    def draw_later_page(canvas, doc):
        canvas.saveState()
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 20*mm, A4[0]/2, 280*mm)
        canvas.restoreState()
        canvas.setFont(base_font, 9)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"- {doc.page} -")
        canvas.drawString(10*mm, 10*mm, "엠베스트 SE 광사드림 학원")

    template_first = PageTemplate(id='First', frames=[frame_first_left, frame_first_right], onPage=draw_first_page)
    template_later = PageTemplate(id='Later', frames=[frame_later_left, frame_later_right], onPage=draw_later_page)

    doc.addPageTemplates([template_first, template_later])

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
    with st.spinner(f"선택된 모델({selected_model_name})로 문제를 출제 중입니다..."):
        
        prompt = f"""
        당신은 엠베스트 SE 영어 강사입니다.
        아래 조건에 맞춰 실제 학교 내신과 동일한 수준의 시험지를 작성하세요.
        
        [출제 범위 정보]
        - 대상: {grade}
        - 교과서: {publisher}
        - 단원: {unit}
        - 문항 수: {num_questions}문항
        - 난이도: {difficulty}
        
        [필수 요청 사항]
        1. **'{publisher}' 교과서의 '{unit}' 단원 내용을 반영해주세요.**
        2. 문제는 수능형(빈칸, 순서, 삽입, 어법, 어휘)과 내신형을 섞어서 출제하세요.
        
        [출력 형식 가이드]
        1. 모든 문제는 '1.', '2.' 숫자로 시작.
        2. 보기: ①, ②, ③, ④, ⑤ 특수문자 사용 (괄호 금지).
        3. 지문이 있는 경우 반드시 [지문] 이라고 표시하고 내용을 작성.
        4. 문제지와 정답지는 '===절취선==='으로 명확히 구분.
        5. 정답지는 '1. 정답: ① / 해설: 상세한 해설' 형식으로 작성.
        
        [작성 시작]
        ===문제지===
        """
        
        try:
            # [핵심] 사이드바에서 선택한 모델 이름을 그대로 사용
            model = genai.GenerativeModel(selected_model_name)
            response = model.generate_content(prompt)
            
            text_data = response.text
            
            if "===절취선===" in text_data:
                parts = text_data.split("===절취선===")
                q_text = parts[0].replace("===문제지===", "").strip()
                a_text = parts[1].replace("===정답지===", "").strip()
            else:
                q_text = text_data
                a_text = "⚠️ 정답지 구분선을 찾지 못했습니다. 전체 내용을 확인해주세요."

            grade_clean = grade.replace("중","").replace("고","")
            
            header_info_q = {
                'title': f"{unit} 단원평가",
                'sub_title': f"[{publisher}] {grade} 내신 1등급 대비",
                'grade': grade_clean
            }
            
            header_info_a = {
                'title': "정답 및 해설",
                'sub_title': f"{unit} 단원평가",
                'grade': "" 
            }

            pdf_q = create_2column_pdf(f"{grade} 시험지", header_info_q, q_text)
            pdf_a = create_2column_pdf(f"{grade} 정답지", header_info_a, a_text)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.success(f"✅ {publisher} 문제지 생성 완료")
                st.download_button("📄 문제지 다운로드", pdf_q, f"엠베스트_{grade}_문제지.pdf", "application/pdf")
            with col_d2:
                st.success("✅ 정답지 생성 완료")
                st.download_button("🔑 정답지 다운로드", pdf_a, f"엠베스트_{grade}_해설지.pdf", "application/pdf")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.warning("팁: 왼쪽 사이드바에서 다른 AI 모델을 선택해보세요.")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: right; color: gray; font-size: 0.8em;'>
        Developed by 엠베스트 SE 광사드림 학원 (Powered by Gemini)
    </div>
    """, 
    unsafe_allow_html=True
)
