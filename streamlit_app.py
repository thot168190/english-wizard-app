import streamlit as st
import google.generativeai as genai
from reportlab.platypus import BaseDocTemplate, Paragraph, Frame, PageTemplate, Table, TableStyle, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import requests
import re
import PyPDF2  # PDF 읽기용 라이브러리 (설치 필요: pip install PyPDF2)

# --------------------------------------------------------------------------
# 1. 초기 설정 및 폰트 자동 설치
# --------------------------------------------------------------------------
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="🏆", layout="wide")

font_path = "NanumGothic.ttf"
font_bold_path = "NanumGothicBold.ttf"

# 폰트 다운로드 함수
def download_font(url, save_path):
    if not os.path.exists(save_path):
        try:
            response = requests.get(url)
            with open(save_path, "wb") as f:
                f.write(response.content)
        except:
            pass

# 나눔고딕 폰트 준비
download_font("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf", font_path)
download_font("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf", font_bold_path)

try:
    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
    pdfmetrics.registerFont(TTFont("NanumGothic-Bold", font_bold_path))
    base_font = "NanumGothic"
    bold_font = "NanumGothic-Bold"
except:
    base_font = "Helvetica"
    bold_font = "Helvetica-Bold"

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --------------------------------------------------------------------------
# 2. UI 구성
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>High-Level 실전 시험지 생성기 (PDF 업로드 지원)</h3>", unsafe_allow_html=True)
st.markdown("---")

if "ws_pdf" not in st.session_state:
    st.session_state.ws_pdf = None
if "ak_pdf" not in st.session_state:
    st.session_state.ak_pdf = None

# [좌측] 옵션 설정
col1, col2, col3 = st.columns(3)
with col1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
with col2:
    if grade == "중1":
        pub_list = ["동아 (윤정미)", "천재 (이재영)", "비상 (김진완)", "미래엔 (최연희)"]
    elif grade == "중2":
        pub_list = ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)", "동아 (윤정미)"]
    elif grade == "고2":
        pub_list = ["YBM (박준언)", "YBM (한상호)", "천재 (이재영)"]
    else:
        pub_list = ["기타 / 공통"]
    publisher = st.selectbox("출판사", pub_list)
with col3:
    unit = st.text_input("단원명", "Lesson 1")

# [중앙] 파일 업로드 기능 추가
st.markdown("### 📂 교과서/본문 자료 업로드")
st.info("가지고 계신 PDF 파일을 아래에 끌어다 놓으세요. AI가 내용을 읽어서 문제를 만듭니다.")

uploaded_file = st.file_uploader("PDF 파일 업로드", type=['pdf'])
source_text = ""

# PDF 텍스트 추출 로직
if uploaded_file is not None:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                source_text += extracted + "\n"
        st.success(f"✅ 파일 내용을 성공적으로 읽었습니다! (총 {len(source_text)}자)")
    except Exception as e:
        st.error(f"PDF 읽기 실패: {e}")

# 텍스트가 없을 경우 직접 입력할 수 있는 공간도 남겨둠
if not source_text:
    source_text = st.text_area("또는 여기에 본문을 직접 붙여넣으셔도 됩니다.", height=150)

# [하단] 문제 유형 설정
c1, c2 = st.columns(2)
with c1:
    q_types = st.multiselect("문제 유형 선택", ["주제/제목", "내용일치", "빈칸추론", "어법상 틀린 것", "어휘 적절성", "순서배열", "문장삽입"], default=["내용일치", "어법상 틀린 것", "빈칸추론"])
with c2:
    num_q = st.slider("문항 수", 5, 30, 20)

# --------------------------------------------------------------------------
# 3. PDF 생성 엔진 (2단, 첫장 헤더, 우측 하단 학원명, 번호/지문 박스)
# --------------------------------------------------------------------------
def create_exam_pdf(header_info, questions_data, is_answer_key=False):
    buffer = BytesIO()
    
    # 문서 설정
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    style_q = ParagraphStyle('Q', parent=styles['Normal'], fontName=base_font, fontSize=10, leading=15)
    style_box_text = ParagraphStyle('BoxText', parent=styles['Normal'], fontName=base_font, fontSize=9, leading=13)

    # 2단 프레임
    frame_w = 92*mm
    gap = 6*mm
    
    # 1페이지 (헤더 공간 확보)
    frame_first_left = Frame(10*mm, 15*mm, frame_w, 225*mm, id='F1_L')
    frame_first_right = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 225*mm, id='F1_R')
    
    # 2페이지 이후 (상단 여백 줄임)
    frame_later_left = Frame(10*mm, 15*mm, frame_w, 265*mm, id='F2_L')
    frame_later_right = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 265*mm, id='F2_R')

    # [1페이지 헤더 그리기]
    def draw_first(canvas, doc):
        canvas.saveState()
        # 타이틀
        canvas.setFont(bold_font, 18)
        canvas.drawCentredString(A4[0]/2, 280*mm, header_info['title'])
        canvas.setFont(base_font, 11)
        canvas.drawCentredString(A4[0]/2, 273*mm, header_info['sub'])
        
        # 결재란 박스
        canvas.setLineWidth(0.8)
        canvas.rect(10*mm, 255*mm, 190*mm, 12*mm)
        canvas.setFont(base_font, 10)
        canvas.drawString(15*mm, 259*mm, f"학년: {header_info['grade']}   |   이름: ________________   |   점수: __________")
        
        # 중앙 점선
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 250*mm)
        
        # 푸터 (우측 하단 학원명)
        canvas.restoreState()
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.drawCentredString(A4[0]/2, 8*mm, f"- {doc.page} -")

    # [2페이지 이후 헤더 그리기 (헤더 없음)]
    def draw_later(canvas, doc):
        canvas.saveState()
        # 중앙 점선
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 285*mm)
        
        # 푸터 (우측 하단 학원명)
        canvas.restoreState()
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.drawCentredString(A4[0]/2, 8*mm, f"- {doc.page} -")

    doc.addPageTemplates([
        PageTemplate(id='First', frames=[frame_first_left, frame_first_right], onPage=draw_first),
        PageTemplate(id='Later', frames=[frame_later_left, frame_later_right], onPage=draw_later)
    ])

    story = []
    
    # 문제 데이터 처리
    for q_idx, q_data in enumerate(questions_data):
        # 1. 지문 박스 (있으면) - 회색 배경
        if q_data.get('passage'):
            p_text = Paragraph(q_data['passage'].replace('\n', '<br/>'), style_box_text)
            t_box = Table([[p_text]], colWidths=[88*mm])
            t_box.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
                ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t_box)
            story.append(Spacer(1, 3*mm))

        # 2. 문제 번호와 내용 (번호 파란색 강조)
        q_num_text = f"<b>{q_idx+1}.</b>"
        q_body_text = q_data['question']
        
        # 보기 처리
        if 'choices' in q_data and q_data['choices']:
            q_body_text += "<br/>" + "<br/>".join(q_data['choices'])
        
        t_question = Table([
            [Paragraph(q_num_text, ParagraphStyle('Num', fontName=bold_font, fontSize=12, textColor=colors.darkblue)),
             Paragraph(q_body_text, style_q)]
        ], colWidths=[8*mm, 82*mm])
        
        t_question.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (0,0), 0),
        ]))
        
        story.append(KeepTogether([t_question, Spacer(1, 5*mm)]))

    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF 생성 중 오류: {e}")
        return None

# --------------------------------------------------------------------------
# 4. AI 파싱 로직
# --------------------------------------------------------------------------
def parse_ai_response(text):
    questions = []
    raw_questions = re.split(r'===문제 \d+===', text)
    
    for raw_q in raw_questions:
        if not raw_q.strip(): continue
        
        q_item = {'passage': '', 'question': '', 'choices': []}
        
        if "[지문]" in raw_q:
            match = re.search(r'\[지문\](.*?)\[/지문\]', raw_q, re.DOTALL)
            if match:
                q_item['passage'] = match.group(1).strip()
                raw_q = raw_q.replace(match.group(0), "")

        choices = []
        lines = raw_q.strip().split('\n')
        q_text_lines = []
        
        for line in lines:
            if re.match(r'[①-⑤]', line.strip()) or re.match(r'\d\)', line.strip()):
                choices.append(line.strip())
            else:
                q_text_lines.append(line.strip())
        
        q_item['question'] = " ".join(q_text_lines).strip()
        q_item['choices'] = choices
        
        if q_item['question']:
            questions.append(q_item)
            
    return questions

# --------------------------------------------------------------------------
# 5. 실행 로직
# --------------------------------------------------------------------------
if st.button("High-Level 시험지 생성", type="primary"):
    if not source_text:
        st.error("본문이 없습니다. PDF를 업로드하거나 텍스트를 입력해주세요.")
    else:
        with st.spinner("AI가 문제를 출제하고 있습니다... (Gemini 2.5 Flash)"):
            prompt = f"""
            당신은 한국의 중고등 영어 내신 전문 강사입니다.
            제공된 [본문]을 바탕으로 {num_q}개의 시험 문제를 만드세요.
            
            [본문]
            {source_text[:10000]} (내용이 너무 길면 일부만 전송됨)
            
            [출제 유형]
            {', '.join(q_types)}
            
            [필수 출력 형식 - 엄격 준수]
            각 문제는 아래 포맷을 정확히 지켜주세요.
            
            ===문제 1===
            [지문]
            (필요하다면 여기에 본문의 일부나 변형된 지문을 넣으세요. 없으면 생략)
            [/지문]
            문제 내용...
            ① choice 1
            ② choice 2
            ③ choice 3
            ④ choice 4
            ⑤ choice 5
            
            ===문제 2===
            ...
            """
            
            try:
                # [요청하신 모델 유지]
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                
                parsed_data = parse_ai_response(response.text)
                
                # 정답지 생성용 (간단히)
                prompt_ans = f"위에서 만든 문제들의 정답과 해설을 알려줘. 형식: 1. 정답 / 해설"
                # response_ans = model.generate_content(prompt_ans) # 필요시 활성화

                header = {'title': f"{unit} 실전 TEST", 'sub': f"{publisher} - {grade} 내신대비", 'grade': grade}
                
                st.session_state.ws_pdf = create_exam_pdf(header, parsed_data)
                
                st.success(f"총 {len(parsed_data)}문항 생성 완료!")
                
            except Exception as e:
                st.error(f"오류 발생: {e}")
                st.info("팁: 모델명이 정확하지 않거나 API 키 문제일 수 있습니다.")

# 다운로드
if st.session_state.ws_pdf:
    st.download_button("📄 시험지 다운로드", st.session_state.ws_pdf, "Final_Exam.pdf", "application/pdf", use_container_width=True)

st.markdown("<br><div style='text-align:right; color:gray'>Developed by 엠베스트 SE 광사드림 학원</div>", unsafe_allow_html=True)
