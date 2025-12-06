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
# 3. PDF 생성 엔진 (디자인 수정됨)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    # 일반 텍스트 스타일
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=10, leading=15)
    
    # [지문 박스 스타일] - 선생님 요청: 회색 배경에 박스 처리
    style_passage = ParagraphStyle('Passage', parent=styles['Normal'], fontName=base_font, fontSize=9.5, leading=14)

    # 레이아웃 프레임
    frame_w = 92*mm
    gap = 6*mm
    
    # 1페이지용 프레임 (상단 헤더 공간 확보)
    frame_f_l = Frame(10*mm, 15*mm, frame_w, 220*mm, id='F1_L')
    frame_f_r = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 220*mm, id='F1_R')
    
    # 2페이지용 프레임 (전체 사용)
    frame_l_l = Frame(10*mm, 15*mm, frame_w, 270*mm, id='F2_L')
    frame_l_r = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 270*mm, id='F2_R')

    def draw_first(canvas, doc):
        canvas.saveState()
        title = header_info['title']
        if doc_type == "answer": title += " [정답 및 해설]"
        
        # 타이틀
        canvas.setFont(bold_font, 18)
        canvas.drawCentredString(A4[0]/2, 280*mm, title)
        canvas.setFont(base_font, 11)
        canvas.drawCentredString(A4[0]/2, 273*mm, header_info['sub'])
        
        # 이름 박스
        canvas.setLineWidth(0.5)
        canvas.rect(10*mm, 255*mm, 190*mm, 12*mm)
        canvas.setFont(base_font, 10)
        canvas.drawString(15*mm, 259*mm, f"학년: {header_info['grade']}    |    이름: ________________    |    점수: __________")
        
        # 구분선 및 로고
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 250*mm)
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    def draw_later(canvas, doc):
        canvas.saveState()
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 285*mm) # 2페이지부터는 길게
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    doc.addPageTemplates([
        PageTemplate(id='First', frames=[frame_f_l, frame_f_r], onPage=draw_first),
        PageTemplate(id='Later', frames=[frame_l_l, frame_l_r], onPage=draw_later)
    ])

    story = []
    
    # 2페이지부터 레이아웃 변경 명령
    story.append(NextPageTemplate('Later'))

    for idx, item in enumerate(items_data):
        if doc_type == "question":
            # 1. [지문 박스] 만들기
            if item.get('passage'):
                # 지문 내용을 박스 안에 넣기
                p = Paragraph(item['passage'].replace("\n", "<br/>"), style_passage)
                t_passage = Table([[p]], colWidths=[88*mm])
                t_passage.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F5F5')), # 연한 회색 배경
                    ('BOX', (0,0), (-1,-1), 0.5, colors.grey), # 테두리
                    ('PADDING', (0,0), (-1,-1), 6), # 안쪽 여백
                ]))
                story.append(t_passage)
                story.append(Spacer(1, 4*mm)) # 지문과 문제 사이 간격

            # 2. [문제 번호 및 내용] - 번호가 사라지지 않도록 Table 구조 확인
            # 번호 (진하게, 파란색)
            num_str = f"<font color='navy'><b>{idx+1}.</b></font>" 
            p_num = Paragraph(num_str, style_normal)
            
            # 문제 내용
            q_content = item['question']
            if item.get('choices'): 
                q_content += "<br/><br/>" + "<br/>".join(item['choices'])
            p_question = Paragraph(q_content, style_normal)

            # 테이블로 번호와 문제를 나란히 배치 (번호 칸: 8mm, 문제 칸: 82mm)
            data = [[p_num, p_question]]
            t_q = Table(data, colWidths=[8*mm, 82*mm])
            t_q.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'), # 위쪽 정렬
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            
            # 잘리지 않게 한 덩어리로 묶음
            story.append(KeepTogether([t_q, Spacer(1, 8*mm)]))
            
        else:
            # 정답지 생성 로직
            num_str = f"<b>{idx+1}.</b>"
            content = f"<b>정답: {item.get('answer', '')}</b><br/><font color='gray' size=9>[해설]</font> {item.get('explanation', '')}"
            data = [[Paragraph(num_str, style_normal), Paragraph(content, style_normal)]]
            t_a = Table(data, colWidths=[8*mm, 82*mm])
            t_a.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
            story.append(KeepTogether([t_a]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------
# 4. AI 파싱 (데이터 정리)
# --------------------------------------------------------------------------
def parse_ai_response(text):
    questions = []
    blocks = text.split("[[문제]]")
    for block in blocks:
        if not block.strip(): continue
        item = {'passage': '', 'question': '', 'choices': [], 'answer': '', 'explanation': ''}
        
        # 지문 추출
        if "[[지문]]" in block and "[[/지문]]" in block:
            parts = block.split("[[/지문]]")
            item['passage'] = parts[0].split("[[지문]]")[1].strip()
            remain = parts[1]
        else:
            remain = block
            
        # 정답 및 해설 추출
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
        
        # 문제 및 보기 분리
        lines = remain.strip().split('\n')
        q_lines = []
        c_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            # 보기는 ①, ② 등이나 숫자로 시작하는 경우
            if re.match(r'^[①-⑤\d]+[\.\)]', line) or line.startswith('①'):
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

c1, c2, c3 = st.columns(3)
with c1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2"])
with c2:
    publisher = st.selectbox("출판사", ["동아 (윤정미)", "동아 (이병민)", "천재 (이재영)", "천재 (정사열)", "비상 (김진완)", "미래엔 (최연희)", "YBM (박준언)"])
with c3:
    unit = st.selectbox("단원", ["1과", "2과", "3과", "4과", "5과", "6과", "7과", "8과"])

# 파일 로딩
loaded_text, is_loaded, file_name = load_textbook(grade, publisher, unit)
st.markdown("---")

if is_loaded:
    source_text = loaded_text
else:
    st.warning(f"⚠️ '{file_name}' 파일 없음 (data 폴더 확인 필요)")
    source_text = st.text_area("직접 본문을 붙여넣으세요.", height=200)

c_opt1, c_opt2 = st.columns(2)
with c_opt1:
    q_types = st.multiselect("출제 유형", ["내용일치", "빈칸추론", "어법", "지칭추론", "순서배열"], default=["내용일치", "빈칸추론", "어법"])
with c_opt2:
    num_q = st.slider("문항 수", 5, 25, 10)

if st.button("시험지 생성 (Start)", type="primary"):
    if not source_text.strip():
        st.error("본문 내용이 없습니다.")
    else:
        target_model_name = "gemini-2.5-flash" 
        with st.spinner(f"AI({target_model_name})가 문제를 출제 중입니다..."):
            
            # [프롬프트] 지문 태그 강조
            prompt = f"""
            당신은 한국의 중학교 영어 내신 시험 출제 위원입니다.
            아래 [본문]을 사용하여 {num_q}문제의 시험지를 만드세요.
            
            [본문]
            {source_text}
            
            [유형] {', '.join(q_types)}
            
            [필수 규칙]
            1. **문제의 질문(발문)은 반드시 '한국어'로 하세요.** (예: "다음 글을 읽고 물음에 답하시오.")
            2. 지문이 필요한 문제는 반드시 [[지문]] ... [[/지문]] 태그로 감싸세요. 
               (이 태그가 있어야 시험지에서 회색 박스로 예쁘게 나옵니다.)
            3. 각 문제는 [[문제]] 태그로 시작하세요.
            4. 문항 번호(1., 2.)는 붙이지 마세요. (코드가 자동으로 붙입니다.)
            5. 정답은 [[정답]], 해설은 [[해설]] 태그를 사용하세요.
            6. 보기는 ①, ②, ③, ④, ⑤ 형식을 사용하세요.
            """
            
            try:
                model = genai.GenerativeModel(target_model_name)
                response = model.generate_content(prompt)
                parsed_data = parse_ai_response(response.text)
                
                if parsed_data:
                    header = {'title': f"{unit} 실전 TEST", 'sub': f"{publisher} - {grade} 내신대비", 'grade': grade}
                    st.session_state.ws_pdf = create_pdf(header, parsed_data, "question")
                    st.session_state.ak_pdf = create_pdf(header, parsed_data, "answer")
                    st.success(f"✅ {len(parsed_data)}문항 출제 완료! (지문 박스 & 번호 복구됨)")
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
