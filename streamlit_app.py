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
# 1. 폰트 및 설정
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
# 2. 데이터 로딩
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
# 3. PDF 생성 엔진 (종이 절약 & 보기 정렬 최적화)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=8*mm, rightMargin=8*mm,
                          topMargin=8*mm, bottomMargin=8*mm)

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=9.5, leading=13)
    style_passage = ParagraphStyle('Passage', parent=styles['Normal'], fontName=base_font, fontSize=9, leading=12)

    frame_w = 95*mm 
    gap = 4*mm      
    
    frame_f_l = Frame(8*mm, 10*mm, frame_w, 230*mm, id='F1_L')
    frame_f_r = Frame(8*mm + frame_w + gap, 10*mm, frame_w, 230*mm, id='F1_R')
    frame_l_l = Frame(8*mm, 10*mm, frame_w, 280*mm, id='F2_L')
    frame_l_r = Frame(8*mm + frame_w + gap, 10*mm, frame_w, 280*mm, id='F2_R')

    def draw_first(canvas, doc):
        canvas.saveState()
        title = header_info['title']
        if doc_type == "answer": title += " [정답 및 해설]"
        
        canvas.setFont(bold_font, 18)
        canvas.drawCentredString(A4[0]/2, 285*mm, title)
        canvas.setFont(base_font, 10)
        canvas.drawCentredString(A4[0]/2, 278*mm, header_info['sub'])
        
        canvas.setLineWidth(0.5)
        canvas.rect(8*mm, 260*mm, 194*mm, 10*mm)
        canvas.setFont(base_font, 9)
        canvas.drawString(12*mm, 263*mm, f"학년: {header_info['grade']}    |    이름: ________________    |    점수: __________")
        
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 10*mm, A4[0]/2, 255*mm)
        canvas.setFont(base_font, 8)
        canvas.drawRightString(200*mm, 5*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    def draw_later(canvas, doc):
        canvas.saveState()
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 10*mm, A4[0]/2, 290*mm)
        canvas.setFont(base_font, 8)
        canvas.drawRightString(200*mm, 5*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    doc.addPageTemplates([
        PageTemplate(id='First', frames=[frame_f_l, frame_f_r], onPage=draw_first),
        PageTemplate(id='Later', frames=[frame_l_l, frame_l_r], onPage=draw_later)
    ])

    story = []
    story.append(NextPageTemplate('Later'))

    for idx, item in enumerate(items_data):
        if doc_type == "question":
            # 지문
            if item.get('passage'):
                p = Paragraph(item['passage'].replace("\n", "<br/>"), style_passage)
                t_passage = Table([[p]], colWidths=[92*mm]) 
                t_passage.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F5F5')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
                    ('PADDING', (0,0), (-1,-1), 4), 
                ]))
                story.append(t_passage)
                story.append(Spacer(1, 2*mm))

            # 문제
            num_str = f"<font color='navy'><b>{idx+1}.</b></font>" 
            p_num = Paragraph(num_str, style_normal)
            
            q_content_text = item['question']
            
            # 보기 처리 (영어 보기 줄바꿈)
            if item.get('choices'): 
                formatted_choices = []
                for choice in item['choices']:
                    formatted_choices.append(f"&nbsp;&nbsp;{choice}")
                choices_block = "<br/>".join(formatted_choices)
                q_content_text += f"<br/>{choices_block}"
                
            p_question = Paragraph(q_content_text, style_normal)

            data = [[p_num, p_question]]
            t_q = Table(data, colWidths=[6*mm, 89*mm])
            t_q.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0), 
                ('BOTTOMPADDING', (0,0), (-1,-1), 0), 
            ]))
            
            story.append(KeepTogether([t_q]))
            story.append(Spacer(1, 3*mm))
            
        else:
            # 정답지
            num_str = f"<b>{idx+1}.</b>"
            content = f"<b>{item.get('answer', '')}</b> &nbsp; <font color='gray' size=8>[해설]</font> {item.get('explanation', '')}"
            data = [[Paragraph(num_str, style_normal), Paragraph(content, style_normal)]]
            t_a = Table(data, colWidths=[6*mm, 89*mm])
            t_a.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
            story.append(KeepTogether([t_a]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------
# 4. AI 파싱
# --------------------------------------------------------------------------
def parse_ai_response(text):
    questions = []
    blocks = text.split("[[문제]]")
    for block in blocks:
        if not block.strip(): continue
        item = {'passage': '', 'question': '', 'choices': [], 'answer': '', 'explanation': ''}
        
        if "[[지문]]" in block and "[[/지문]]" in block:
            parts = block.split("[[/지문]]")
            item['passage'] = parts[0].split("[[지문]]")[1].strip()
            remain = parts[1]
        else:
            remain = block
            
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
        
        lines = remain.strip().split('\n')
        q_lines = []
        c_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if re.match(r'^[\(]?[①-⑤\d]+[\.\)]', line) or line.startswith('①'):
                c_lines.append(line)
            else:
                q_lines.append(line)
        item['question'] = " ".join(q_lines)
        item['choices'] = c_lines
        if item['question']: questions.append(item)
    return questions

# --------------------------------------------------------------------------
# 5. UI 화면
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>High-Level 실전 시험지 마법사</h3>", unsafe_allow_html=True)

if "ws_pdf" not in st.session_state: st.session_state.ws_pdf = None
if "ak_pdf" not in st.session_state: st.session_state.ak_pdf = None

# 상단 설정
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
    st.warning(f"⚠️ '{file_name}' 파일 없음")
    source_text = st.text_area("직접 본문을 붙여넣으세요.", height=200)

# 옵션 설정 (난이도 추가됨)
c_opt1, c_opt2, c_opt3 = st.columns([2, 1, 1])
with c_opt1:
    q_types = st.multiselect("출제 유형", ["내용일치", "빈칸추론", "어법", "지칭추론", "순서배열", "문장삽입"], default=["내용일치", "빈칸추론", "어법"])
with c_opt2:
    difficulty = st.select_slider("난이도", options=["하 (기초)", "중 (내신표준)", "상 (킬러문항)"], value="중 (내신표준)")
with c_opt3:
    num_q = st.slider("문항 수", 5, 25, 10)

if st.button("시험지 생성 (Start)", type="primary"):
    if not source_text.strip():
        st.error("본문 내용이 없습니다.")
    else:
        target_model_name = "gemini-2.5-flash" 
        with st.spinner(f"AI({target_model_name})가 최신 경향 문제를 출제 중입니다..."):
            
            # [프롬프트 핵심 수정]
            # 1. 난이도 반영
            # 2. 발문(질문)은 한국어, 선지(보기)는 영어로 강제
            prompt = f"""
            당신은 대한민국 '대치동' 스타일의 중학교 영어 내신 전문 출제위원입니다.
            [본문]을 바탕으로 {num_q}문제의 실전 시험지를 만드세요.
            
            [본문]
            {source_text}
            
            [설정]
            - 난이도: {difficulty}
            - 유형: {', '.join(q_types)}
            
            [필수 출제 규칙 - 이것을 어기면 안됨]
            1. **발문(Question)은 반드시 '한국어'로 작성하세요.** (예: "다음 글의 내용과 일치하는 것은?")
            2. **선지(Answer Choices)는 반드시 '영어'로 작성하세요.** (단, 해석 문제는 제외)
               - 예: ① Jihun plays the guitar. (O)
               - 예: ① 지훈이는 기타를 친다. (X - 절대 금지)
            3. 매번 새로운 유형의 문제를 창작하세요. (단순 복사 금지)
            4. 지문이 필요한 문제는 [[지문]]...[[/지문]] 태그를 사용하세요.
            5. 각 문제는 [[문제]] 태그로 시작하세요.
            6. 보기는 ①, ②, ③, ④, ⑤ 형식을 사용하세요.
            7. 정답은 [[정답]], 해설은 [[해설]] 태그를 사용하세요.
            """
            
            try:
                model = genai.GenerativeModel(target_model_name)
                response = model.generate_content(prompt)
                parsed_data = parse_ai_response(response.text)
                
                if parsed_data:
                    header = {'title': f"{unit} 실전 TEST", 'sub': f"{publisher} - {grade} 내신대비 ({difficulty})", 'grade': grade}
                    st.session_state.ws_pdf = create_pdf(header, parsed_data, "question")
                    st.session_state.ak_pdf = create_pdf(header, parsed_data, "answer")
                    st.success(f"✅ {len(parsed_data)}문항 출제 완료! (난이도: {difficulty}, 선지 영어 적용)")
                else:
                    st.error("AI 응답 분석 실패. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"오류: {e}")

if st.session_state.ws_pdf and st.session_state.ak_pdf:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button("📄 문제지 다운로드", st.session_state.ws_pdf, "Test_Paper.pdf", "application/pdf", use_container_width=True)
    with col_d2:
        st.download_button("🔑 정답지 다운로드", st.session_state.ak_pdf, "Answer_Key.pdf", "application/pdf", use_container_width=True)

st.caption("Developed by 엠베스트 SE 광사드림 학원")
