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

# --------------------------------------------------------------------------
# 1. 폰트 및 설정 (나눔고딕)
# --------------------------------------------------------------------------
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="🏆", layout="wide")

font_path = "NanumGothic.ttf"
font_bold_path = "NanumGothicBold.ttf"

def download_font(url, save_path):
    if not os.path.exists(save_path):
        try:
            response = requests.get(url)
            with open(save_path, "wb") as f:
                f.write(response.content)
        except:
            pass

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

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
elif "GOOGLE_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
else:
    st.error("API 키가 설정되지 않았습니다.")

# --------------------------------------------------------------------------
# 2. 교과서 데이터 로딩 함수
# --------------------------------------------------------------------------
def load_textbook(grade, publisher, unit):
    pub_map = {
        "동아 (윤정미)": "동아윤", "동아 (이병민)": "동아이",
        "천재 (이재영)": "천재이", "천재 (정사열)": "천재정",
        "비상 (김진완)": "비상김", "미래엔 (최연희)": "미래엔",
        "YBM (박준언)": "YBM박", "YBM (한상호)": "YBM한"
    }
    pub_code = pub_map.get(publisher, "기타")
    unit_code = "1과" 
    if "2" in unit: unit_code = "2과"
    elif "3" in unit: unit_code = "3과"
    elif "4" in unit: unit_code = "4과"
    elif "5" in unit: unit_code = "5과"
    elif "6" in unit: unit_code = "6과"
    elif "7" in unit: unit_code = "7과"
    elif "8" in unit: unit_code = "8과"

    file_name = f"{grade}_{pub_code}_{unit_code}.txt"
    file_path = os.path.join("data", file_name)
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read(), True, file_name
    return "", False, file_name

# --------------------------------------------------------------------------
# 3. PDF 생성 엔진 (Exam4You 디자인 핵심)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    
    # [페이지 설정] 상단 여백을 충분히(28mm) 주어 헤더 공간 확보
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=28*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    # 일반 텍스트 (줄간격 14)
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=9.5, leading=14)
    # 지문 박스 내부 텍스트
    style_passage = ParagraphStyle('Passage', parent=styles['Normal'], fontName=base_font, fontSize=9, leading=13)

    # [2단 레이아웃 계산]
    # A4 폭(210) - 좌우여백(20) = 190mm
    # 단 간격 10mm -> 각 단의 너비는 90mm
    col_width = 90*mm
    col_gap = 10*mm
    
    frame_l = Frame(10*mm, 15*mm, col_width, 250*mm, id='F1')
    frame_r = Frame(10*mm + col_width + col_gap, 15*mm, col_width, 250*mm, id='F2')

    # [헤더 및 배경 그리기] - 매 페이지마다 실행
    def draw_page(canvas, doc):
        canvas.saveState()
        
        # 1. 헤더 (파란색 박스 디자인)
        blue_color = colors.HexColor("#2F74B5") # 이그잼포유 스타일 파랑
        
        # (1) 왼쪽 상단: 교과서/단원 박스
        canvas.setFillColor(blue_color)
        canvas.rect(10*mm, 280*mm, 50*mm, 10*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(bold_font, 11)
        # 텍스트 가운데 정렬
        canvas.drawCentredString(35*mm, 283*mm, f"{header_info['publisher']} {header_info['unit']}")
        
        # (2) 학년 표시 바 (회색)
        canvas.setFillColor(colors.lightgrey)
        canvas.rect(10*mm, 274*mm, 50*mm, 6*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.setFont(bold_font, 9)
        canvas.drawCentredString(35*mm, 276*mm, header_info['grade'])
        
        # (3) 오른쪽 상단: 시험지 제목
        canvas.setFillColor(blue_color)
        canvas.setFont(bold_font, 16)
        canvas.drawRightString(200*mm, 280*mm, header_info['title'])
        
        # (4) 헤더 밑줄 (파란색 굵게)
        canvas.setStrokeColor(blue_color)
        canvas.setLineWidth(1.5)
        canvas.line(10*mm, 272*mm, 200*mm, 272*mm)
        
        # 2. 가운데 점선 (절취선)
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.5)
        canvas.setDash(2, 2)
        mid_x = 105*mm # A4 중앙
        canvas.line(mid_x, 15*mm, mid_x, 265*mm)
        
        # 3. 하단 (페이지 번호 & 로고)
        canvas.setDash(1, 0) # 점선 해제
        canvas.setFillColor(colors.black)
        canvas.setFont(base_font, 9)
        page_num = doc.page
        canvas.drawCentredString(A4[0]/2, 8*mm, f"- {page_num} -")
        
        # 우측 하단 로고
        canvas.setFillColor(colors.HexColor("#469C36")) # 이그잼포유 녹색
        canvas.setFont(bold_font, 10)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        
        canvas.restoreState()

    doc.addPageTemplates([
        PageTemplate(id='TwoCol', frames=[frame_l, frame_r], onPage=draw_page),
    ])

    story = []
    
    for idx, item in enumerate(items_data):
        # ------------------------------------------------------------------
        # [문제 레이아웃 구성]
        # Table 구조: [[ 번호칸(7mm), 내용칸(83mm) ]]
        # 이렇게 해야 번호가 질문 왼쪽에 독립적으로 딱 붙습니다.
        # ------------------------------------------------------------------
        
        content_elements = []
        
        # 1. 지문 박스 (있을 경우 최상단)
        if doc_type == "question" and item.get('passage'):
            # 줄바꿈 처리
            pass_text = item['passage'].replace("\n", "<br/>")
            p_pass = Paragraph(pass_text, style_passage)
            
            # 박스 스타일 (회색 배경 + 테두리)
            t_pass = Table([[p_pass]], colWidths=[80*mm])
            t_pass.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke), 
                ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            content_elements.append(t_pass)
            content_elements.append(Spacer(1, 3*mm))

        # 2. 질문 (발문)
        q_text = item['question']
        p_question = Paragraph(q_text, style_normal)
        content_elements.append(p_question)
        
        # 3. 보기 (선지)
        if doc_type == "question" and item.get('choices'):
            choices_html = ""
            for c in item['choices']:
                # 보기마다 줄바꿈 + 들여쓰기(&nbsp;)
                choices_html += f"<br/>&nbsp;&nbsp;{c}"
            
            p_choices = Paragraph(choices_html, style_normal)
            content_elements.append(p_choices)
            
        # 4. 문항 번호 (파란색, 굵게)
        if doc_type == "question":
            # 이그잼포유 스타일: 짙은 파랑(#2F74B5), 폰트 11
            num_html = f"<font color='#2F74B5' size='11'><b>{idx+1}.</b></font>"
        else:
            num_html = f"<b>{idx+1}.</b>" # 정답지는 그냥 검은색

        p_num = Paragraph(num_html, style_normal)
        
        # [메인 테이블 조립]
        # 왼쪽 칸: 번호, 오른쪽 칸: [지문+질문+보기] 덩어리
        row_data = [[p_num, content_elements]]
        
        t_main = Table(row_data, colWidths=[8*mm, 82*mm])
        t_main.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'), # 번호는 항상 위쪽에 정렬
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # 문제 하나를 통째로 묶어서(KeepTogether) 페이지 넘어갈 때 잘리지 않게 함
        story.append(KeepTogether([t_main]))
        story.append(Spacer(1, 5*mm)) # 문제 사이 간격

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------
# 4. AI 응답 파싱
# --------------------------------------------------------------------------
def parse_ai_response(text):
    questions = []
    blocks = text.split("[[문제]]")
    for block in blocks:
        if not block.strip(): continue
        item = {'passage': '', 'question': '', 'choices': [], 'answer': '', 'explanation': ''}
        
        # 지문 파싱
        if "[[지문]]" in block and "[[/지문]]" in block:
            parts = block.split("[[/지문]]")
            item['passage'] = parts[0].split("[[지문]]")[1].strip()
            remain = parts[1]
        else:
            remain = block
            
        # 정답/해설 파싱
        if "[[정답]]" in remain:
            parts = remain.split("[[정답]]")
            content_part = parts[0]
            ans_part = parts[1]
            if "[[해설]]" in ans_part:
                ans_split = ans_part.split("[[해설]]")
                item['answer'] = ans_split[0].strip()
                item['explanation'] = ans_split[1].strip()
            else:
                item['answer'] = ans_part.strip()
            remain = content_part
        
        # 질문/보기 분리
        lines = remain.strip().split('\n')
        q_lines = []
        c_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 보기 감지 (①, (1), 1. a. 등 다양한 형식)
            is_choice = False
            if re.match(r'^[\(]?[①-⑮\d]+[\.\)]', line): is_choice = True
            if line.startswith('①'): is_choice = True
            if re.match(r'^[a-eA-E][\.\)]', line): is_choice = True
            
            if is_choice:
                c_lines.append(line)
            else:
                # AI가 만든 번호(1. 2.) 제거 -> 우리가 파란색으로 붙일 거니까
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                q_lines.append(cleaned)
                
        item['question'] = " ".join(q_lines)
        item['choices'] = c_lines
        if item['question']: questions.append(item)
    return questions

# --------------------------------------------------------------------------
# 5. Streamlit UI
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#2F74B5;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>High-Level 내신대비 문제 출제기</h3>", unsafe_allow_html=True)

if "ws_pdf" not in st.session_state: st.session_state.ws_pdf = None
if "ak_pdf" not in st.session_state: st.session_state.ak_pdf = None

c1, c2, c3 = st.columns(3)
with c1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2"])
with c2:
    publisher = st.selectbox("출판사", ["동아 (윤정미)", "동아 (이병민)", "천재 (이재영)", "천재 (정사열)", "비상 (김진완)", "미래엔 (최연희)", "YBM (박준언)"])
with c3:
    unit = st.selectbox("단원", ["1과", "2과", "3과", "4과", "5과", "6과", "7과", "8과"])

loaded_text, is_loaded, file_name = load_textbook(grade, publisher, unit)
st.markdown("---")

if is_loaded:
    source_text = loaded_text
else:
    st.warning(f"⚠️ '{file_name}' 파일이 없습니다.")
    source_text = st.text_area("직접 본문을 붙여넣으세요.", height=150)

# 옵션 설정
c_opt1, c_opt2, c_opt3 = st.columns([2, 1, 1])
with c_opt1:
    q_types = st.multiselect("출제 유형", ["내용일치", "빈칸추론", "어법", "지칭추론", "순서배열", "문장삽입"], default=["내용일치", "빈칸추론", "어법"])
with c_opt2:
    difficulty = st.select_slider("난이도", options=["하", "중", "상"], value="중")
with c_opt3:
    num_q = st.slider("문항 수", 5, 20, 10)

if st.button("시험지 생성 (Start)", type="primary", use_container_width=True):
    if not source_text.strip():
        st.error("본문 내용이 없습니다.")
    else:
        target_model_name = "gemini-2.5-flash"
        with st.spinner(f"AI({target_model_name})가 이그잼포유 스타일로 문제를 만들고 있습니다..."):
            
            # [프롬프트] 선생님 요청사항 반영
            # 1. 질문은 한국어
            # 2. 보기는 영어
            prompt = f"""
            당신은 한국의 중학교 영어 내신 전문 출제위원입니다.
            [본문]을 바탕으로 {num_q}문제의 실전 시험지를 만드세요.
            
            [본문]
            {source_text}
            
            [설정]
            - 난이도: {difficulty}
            - 유형: {', '.join(q_types)}
            
            [필수 출제 규칙]
            1. **질문(발문)은 반드시 '한국어'로 작성하세요.** (예: "다음 글의 내용과 일치하지 않는 것은?")
            2. **보기(선지)는 '영어'로 작성하세요.** (영어 시험의 퀄리티를 위해 필수)
               - 단, 해석 문제나 영작 문제는 예외적으로 한국어 보기 가능.
               - 형식: ① Choice 1  ② Choice 2 ...
            3. **지문 박스:** 지문이 필요한 문제는 반드시 [[지문]] ...본문... [[/지문]] 태그를 사용하세요.
            4. **태그:** 각 문제는 [[문제]] 태그로 시작. 정답은 [[정답]], 해설은 [[해설]].
            5. 문항 번호(1., 2.)는 텍스트에 포함하지 마세요. (자동 생성됨)
            """
            
            try:
                model = genai.GenerativeModel(target_model_name)
                response = model.generate_content(prompt)
                parsed_data = parse_ai_response(response.text)
                
                if parsed_data:
                    # 헤더 정보
                    header = {
                        'publisher': publisher.split()[0], 
                        'unit': unit,
                        'title': "예상문제 1회",
                        'grade': grade
                    }
                    
                    st.session_state.ws_pdf = create_pdf(header, parsed_data, "question")
                    st.session_state.ak_pdf = create_pdf(header, parsed_data, "answer")
                    st.success(f"✅ {len(parsed_data)}문항 출제 완료! (디자인: 파란 번호, 2단 편집, 한글 질문)")
                else:
                    st.error("AI 응답 분석 실패. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"오류: {e}")

if st.session_state.ws_pdf and st.session_state.ak_pdf:
    st.divider()
    c_d1, c_d2 = st.columns(2)
    with c_d1:
        st.download_button("📄 시험지 다운로드", st.session_state.ws_pdf, "Exam_Paper.pdf", "application/pdf", use_container_width=True)
    with c_d2:
        st.download_button("🔑 정답지 다운로드", st.session_state.ak_pdf, "Answer_Key.pdf", "application/pdf", use_container_width=True)

st.caption("Developed by 엠베스트 SE 광사드림 학원")
