import streamlit as st
import google.generativeai as genai
from reportlab.platypus import BaseDocTemplate, Paragraph, Frame, PageTemplate, Table, TableStyle, Spacer, KeepTogether, NextPageTemplate
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
# 1. 폰트 및 기본 설정
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
# 2. 교과서 데이터 로딩
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
# 3. PDF 생성 엔진 (Exam4You 스타일 2단 편집)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    
    # 여백 설정 (좌우 여백을 조금 넉넉히 주어 2단 편집 시 답답하지 않게)
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    # 기본 텍스트 스타일
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=9.5, leading=14)
    # 지문 스타일 (약간 작게)
    style_passage = ParagraphStyle('Passage', parent=styles['Normal'], fontName=base_font, fontSize=9, leading=13)

    # 2단 프레임 계산
    # A4 너비 210mm - 좌우여백 20mm = 190mm 사용 가능
    # 190 / 2 = 95mm. 중간 간격 10mm 뺌 -> 한 단 너비 약 90mm
    col_width = 90*mm
    col_gap = 10*mm
    
    # 1페이지용 프레임 (헤더 공간 확보)
    frame_f_l = Frame(10*mm, 10*mm, col_width, 230*mm, id='F1_L')
    frame_f_r = Frame(10*mm + col_width + col_gap, 10*mm, col_width, 230*mm, id='F1_R')
    
    # 2페이지용 프레임 (전체 사용)
    frame_l_l = Frame(10*mm, 10*mm, col_width, 275*mm, id='F2_L')
    frame_l_r = Frame(10*mm + col_width + col_gap, 10*mm, col_width, 275*mm, id='F2_R')

    # [배경 그리기 함수] - 헤더 및 가운데 점선 그리기
    def draw_first(canvas, doc):
        canvas.saveState()
        
        # 1. 타이틀 (중앙 정렬)
        title = header_info['title']
        if doc_type == "answer": title += " [정답 및 해설]"
        canvas.setFont(bold_font, 16)
        canvas.drawCentredString(A4[0]/2, 280*mm, title)
        canvas.setFont(base_font, 10)
        canvas.drawCentredString(A4[0]/2, 273*mm, header_info['sub'])
        
        # 2. 이름/점수 박스 (실제 시험지처럼 깔끔하게)
        canvas.setLineWidth(0.8) # 박스 테두리 약간 굵게
        canvas.rect(10*mm, 255*mm, 190*mm, 12*mm)
        canvas.setFont(bold_font, 10)
        canvas.drawString(15*mm, 259*mm, f"학년: {header_info['grade']}    |    이름: ________________________    |    점수: __________")
        
        # 3. 가운데 점선 (절취선)
        canvas.setLineWidth(0.5)
        canvas.setDash(2, 2) # 점선 패턴
        mid_x = 105*mm # A4 절반
        canvas.line(mid_x, 10*mm, mid_x, 250*mm) # 헤더 아래부터 바닥까지
        
        # 4. 학원 로고
        canvas.setFont(base_font, 8)
        canvas.drawRightString(200*mm, 5*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    def draw_later(canvas, doc):
        canvas.saveState()
        # 2페이지부터는 점선을 끝까지 길게
        mid_x = 105*mm
        canvas.setLineWidth(0.5)
        canvas.setDash(2, 2)
        canvas.line(mid_x, 10*mm, mid_x, 285*mm)
        
        canvas.setFont(base_font, 8)
        canvas.drawRightString(200*mm, 5*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    doc.addPageTemplates([
        PageTemplate(id='First', frames=[frame_f_l, frame_f_r], onPage=draw_first),
        PageTemplate(id='Later', frames=[frame_l_l, frame_l_r], onPage=draw_later)
    ])

    story = []
    # 첫 페이지 프레임이 차면 자동으로 Later 템플릿으로 넘어감
    # (NextPageTemplate은 명시적으로 페이지를 넘길 때 쓰지만, 여기선 자연스럽게 흐르도록 둠)
    
    for idx, item in enumerate(items_data):
        # -----------------------------------------------------------
        # [구조] 2칸 테이블 사용: [번호칸] | [문제내용칸]
        # 이렇게 해야 번호가 들쑥날쑥하지 않고 왼쪽에 딱 고정됨.
        # -----------------------------------------------------------
        
        content_elements = []
        
        # 1. 지문 (있으면 문제 내용 칸에 먼저 추가)
        if doc_type == "question" and item.get('passage'):
            p = Paragraph(item['passage'].replace("\n", "<br/>"), style_passage)
            # 지문 박스 스타일
            t_passage = Table([[p]], colWidths=[80*mm]) # 번호칸 제외한 너비
            t_passage.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 0.5, colors.black), # 검은 테두리
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke), # 연한 회색 배경
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            content_elements.append(t_passage)
            content_elements.append(Spacer(1, 2*mm))

        # 2. 문제 텍스트 (발문)
        q_text = item['question']
        # 보기 처리 (한글 질문 밑에 영어 보기들)
        if doc_type == "question" and item.get('choices'):
            q_text += "<br/>" # 질문과 보기 사이 간격
            for choice in item['choices']:
                # 들여쓰기(&nbsp;)를 넣어 보기 좋게
                q_text += f"<br/>&nbsp;&nbsp;{choice}"
        
        p_question = Paragraph(q_text, style_normal)
        content_elements.append(p_question)

        # 3. [번호] 와 [내용]을 담은 메인 테이블 생성
        # 번호 스타일: 파란색(Navy), 굵게, 폰트 11
        if doc_type == "question":
            num_str = f"<font color='navy' size='11'><b>{idx+1}.</b></font>"
        else:
            num_str = f"<b>{idx+1}.</b>" # 정답지는 검은색
            
        p_num = Paragraph(num_str, style_normal)
        
        # 테이블 구성: 왼쪽(6mm) 오른쪽(84mm)
        row_data = [[p_num, content_elements]] 
        
        t_main = Table(row_data, colWidths=[7*mm, 83*mm])
        t_main.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'), # 번호가 항상 맨 위에 위치
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        story.append(KeepTogether([t_main])) # 문제 하나가 페이지 넘김에 잘리지 않도록
        
        # 문제 사이 간격 (종이 절약을 위해 적당히 좁힘)
        story.append(Spacer(1, 4*mm))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------
# 4. AI 파싱 로직
# --------------------------------------------------------------------------
def parse_ai_response(text):
    questions = []
    # AI가 번호를 1. 2. 이렇게 줄 수도 있고 안 줄 수도 있음. [[문제]] 태그 기준으로 자름
    blocks = text.split("[[문제]]")
    
    for block in blocks:
        if not block.strip(): continue
        item = {'passage': '', 'question': '', 'choices': [], 'answer': '', 'explanation': ''}
        
        # 1. 지문 파싱
        if "[[지문]]" in block and "[[/지문]]" in block:
            parts = block.split("[[/지문]]")
            passage_content = parts[0].split("[[지문]]")[1].strip()
            item['passage'] = passage_content
            remain = parts[1]
        else:
            remain = block
            
        # 2. 정답/해설 파싱
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
        
        # 3. 질문 및 보기 분리
        lines = remain.strip().split('\n')
        q_lines = []
        c_lines = []
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 보기 감지 (①, 1), (1), a. b. 등 다양한 케이스 대응)
            # 영어 보기의 경우 AI가 "1. Apple" 처럼 줄 수 있으므로 정교한 정규식 필요
            is_choice = False
            if re.match(r'^[\(]?[①-⑮\d]+[\.\)]', line): is_choice = True
            if line.startswith('①'): is_choice = True
            if re.match(r'^[a-eA-E][\.\)]', line): is_choice = True
            
            if is_choice:
                c_lines.append(line)
            else:
                # 문항 번호(1. 2.)가 질문 앞에 붙어있으면 제거 (우리가 따로 붙일 거니까)
                cleaned_line = re.sub(r'^\d+[\.\)]\s*', '', line)
                q_lines.append(cleaned_line)
                
        item['question'] = " ".join(q_lines)
        item['choices'] = c_lines
        
        if item['question']: 
            questions.append(item)
            
    return questions

# --------------------------------------------------------------------------
# 5. UI 화면 구성
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>High-Level 실전 시험지 마법사 (Pro Ver.)</h3>", unsafe_allow_html=True)

if "ws_pdf" not in st.session_state: st.session_state.ws_pdf = None
if "ak_pdf" not in st.session_state: st.session_state.ak_pdf = None

# 상단 선택 바
c1, c2, c3 = st.columns(3)
with c1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2"])
with c2:
    publisher = st.selectbox("출판사", ["동아 (윤정미)", "동아 (이병민)", "천재 (이재영)", "천재 (정사열)", "비상 (김진완)", "미래엔 (최연희)", "YBM (박준언)"])
with c3:
    unit = st.selectbox("단원", ["1과", "2과", "3과", "4과", "5과", "6과", "7과", "8과"])

loaded_text, is_loaded, file_name = load_textbook(grade, publisher, unit)
st.markdown("---")

# 본문 로딩 상태
if is_loaded:
    source_text = loaded_text
else:
    st.warning(f"⚠️ '{file_name}' 파일이 없습니다.")
    source_text = st.text_area("직접 본문을 붙여넣으세요.", height=150)

# 옵션 설정
c_opt1, c_opt2, c_opt3 = st.columns([2, 1, 1])
with c_opt1:
    q_types = st.multiselect("출제 유형", ["내용일치", "빈칸추론", "어법", "지칭추론", "순서배열", "문장삽입", "주제찾기"], default=["내용일치", "빈칸추론", "어법"])
with c_opt2:
    difficulty = st.select_slider("난이도", options=["하", "중", "상"], value="중")
with c_opt3:
    num_q = st.slider("문항 수", 5, 20, 8)

# 생성 버튼
if st.button("시험지 생성 (Start)", type="primary", use_container_width=True):
    if not source_text.strip():
        st.error("본문 내용이 없습니다.")
    else:
        target_model_name = "gemini-2.5-flash" 
        with st.spinner(f"AI({target_model_name})가 대치동 스타일로 문제를 출제 중입니다..."):
            
            # [프롬프트] - 선생님 요청 사항 완벽 반영
            prompt = f"""
            당신은 한국의 중학교 영어 내신 전문 출제위원입니다.
            [본문]을 바탕으로 {num_q}문제의 실전 시험지를 만드세요.
            
            [본문]
            {source_text}
            
            [설정]
            - 난이도: {difficulty}
            - 유형: {', '.join(q_types)}
            
            [필수 출제 규칙]
            1. **발문(Question)은 반드시 '한국어'로 작성.** (예: "다음 글을 읽고 물음에 답하시오.")
            2. **선지(Choices)는 반드시 '영어'로 작성.** (단, 해석 문제는 한국어 가능)
               - 보기 형식: ① Choice 1  ② Choice 2 ... (줄바꿈은 Python 코드가 처리함)
            3. **지문 박스 처리:** 지문이 필요한 문제는 반드시 [[지문]] ...본문내용... [[/지문]] 태그로 감쌀 것.
            4. **태그 필수:** 각 문제는 [[문제]] 태그로 시작.
            5. 정답은 [[정답]], 해설은 [[해설]] 태그 사용.
            6. 문항 번호(1., 2.)는 텍스트에 포함하지 말 것. (자동 생성됨)
            """
            
            try:
                model = genai.GenerativeModel(target_model_name)
                response = model.generate_content(prompt)
                parsed_data = parse_ai_response(response.text)
                
                if parsed_data:
                    # PDF 생성
                    header = {'title': f"{unit} 실전 TEST", 'sub': f"{publisher} - {grade} 내신대비 ({difficulty})", 'grade': grade}
                    st.session_state.ws_pdf = create_pdf(header, parsed_data, "question")
                    st.session_state.ak_pdf = create_pdf(header, parsed_data, "answer")
                    st.success(f"✅ {len(parsed_data)}문항 출제 완료! (디자인: 2단 편집, 파란색 번호, 지문 박스)")
                else:
                    st.error("AI 응답 분석 실패. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"오류: {e}")

# 다운로드 버튼
if st.session_state.ws_pdf and st.session_state.ak_pdf:
    st.divider()
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button("📄 문제지 다운로드 (PDF)", st.session_state.ws_pdf, "Final_Exam_Paper.pdf", "application/pdf", use_container_width=True)
    with col_d2:
        st.download_button("🔑 정답지 다운로드 (PDF)", st.session_state.ak_pdf, "Answer_Key.pdf", "application/pdf", use_container_width=True)

st.caption("Developed by 엠베스트 SE 광사드림 학원")
