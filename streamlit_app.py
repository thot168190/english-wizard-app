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
# 1. 설정 및 폰트
# --------------------------------------------------------------------------
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="🏆", layout="wide")

font_path = "NanumGothic.ttf"
font_bold_path = "NanumGothicBold.ttf"

# 한글 폰트 다운로드 함수
def download_font(url, save_path):
    if not os.path.exists(save_path):
        try:
            response = requests.get(url)
            with open(save_path, "wb") as f:
                f.write(response.content)
        except:
            pass

# 나눔고딕 폰트 다운로드
download_font("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf", font_path)
download_font("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf", font_bold_path)

# 폰트 등록
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
# 3. PDF 생성 엔진 (여기가 핵심 수정됨!)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    
    # 여백 설정: 위쪽 여백을 조금 줄여서 내용을 더 많이 담음
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=10, leading=16)
    style_box = ParagraphStyle('Box', parent=styles['Normal'], fontName=base_font, fontSize=9.5, leading=14)

    # 2단 레이아웃 프레임 설정
    frame_w = 92*mm
    gap = 6*mm
    
    # [Page 1 용] - 위쪽에 타이틀 공간(40mm)을 비워둠
    frame_f_l = Frame(10*mm, 15*mm, frame_w, 220*mm, id='F1_L') 
    frame_f_r = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 220*mm, id='F1_R')
    
    # [Page 2 이후 용] - 위쪽까지 꽉 채움 (높이 270mm)
    frame_l_l = Frame(10*mm, 15*mm, frame_w, 270*mm, id='F2_L')
    frame_l_r = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 270*mm, id='F2_R')

    # [1페이지 그리기 함수] : 타이틀 + 이름 박스 그림
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
        
        # 가운데 점선 (구분선)
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 250*mm)
        
        # 하단 로고
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    # [2페이지 이후 그리기 함수] : 타이틀 없이 점선과 로고만 그림
    def draw_later(canvas, doc):
        canvas.saveState()
        
        # 가운데 점선 (위쪽 끝까지 길게)
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 285*mm) 
        
        # 하단 로고
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    # 템플릿 등록 (First가 기본, Later는 다음 페이지부터)
    doc.addPageTemplates([
        PageTemplate(id='First', frames=[frame_f_l, frame_f_r], onPage=draw_first),
        PageTemplate(id='Later', frames=[frame_l_l, frame_l_r], onPage=draw_later)
    ])

    story = []
    
    # [핵심] 첫 페이지 내용이 끝나면 자동으로 'Later' 템플릿(2페이지용)으로 넘어가라고 지시
    story.append(NextPageTemplate('Later'))

    for idx, item in enumerate(items_data):
        if doc_type == "question":
            # 지문 박스
            if item.get('passage'):
                p = Paragraph(item['passage'].replace("\n", "<br/>"), style_box)
                t = Table([[p]], colWidths=[88*mm])
                t.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke), ('PADDING', (0,0), (-1,-1), 5)]))
                story.append(t)
                story.append(Spacer(1, 3*mm))
            
            # 문제 내용
            num_text = f"<font color='darkblue'><b>{idx+1}.</b></font>"
            q_text = item['question']
            
            # 보기가 있으면 추가
            if item.get('choices'): 
                q_text += "<br/><br/>" + "<br/>".join(item['choices'])
                
            data = [[Paragraph(num_text, style_normal), Paragraph(q_text, style_normal)]]
            t_q = Table(data, colWidths=[8*mm, 82*mm])
            t_q.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(KeepTogether([t_q, Spacer(1, 6*mm)]))
        else:
            # 정답지
            num_text = f"<b>{idx+1}.</b>"
            content = f"<b>정답: {item.get('answer', '')}</b><br/><font color='gray'>[해설]</font> {item.get('explanation', '')}"
            data = [[Paragraph(num_text, style_normal), Paragraph(content, style_normal)]]
            t_a = Table(data, colWidths=[8*mm, 82*mm])
            t_a.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
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

# [파일 자동 로딩]
loaded_text, is_loaded, file_name = load_textbook(grade, publisher, unit)

st.markdown("---")
if is_loaded:
    # 화면에 본문 출력 X, 녹색 알림 메시지 X (내부적으로만 처리)
    source_text = loaded_text
else:
    st.warning(f"⚠️ '{file_name}' 파일이 아직 없습니다. (경로: data/{file_name})")
    st.info("좌측 파일 목록에서 'data' 폴더를 만들고, 해당 이름으로 파일을 만들어 본문을 붙여넣어 주세요.")
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
            # 프롬프트 강력 수정 (한국어 발문 강제)
            prompt = f"""
            당신은 한국의 중학교 영어 내신 시험 출제 위원입니다.
            [본문]을 바탕으로 {num_q}개의 문제를 만드세요.
            
            [본문]
            {source_text}
            
            [유형] {', '.join(q_types)}
            
            [매우 중요한 규칙]
            1. **문제의 질문(발문)은 반드시 '한국어'로 작성하십시오.** (예: "Choose the correct sentence" -> "다음 중 어법상 옳은 문장은?")
            2. 영어 지문과 보기를 제외한 모든 설명은 한국어로 하세요.
            3. 인삿말 금지. 바로 데이터 출력.
            4. 각 문제는 [[문제]] 태그로 시작.
            5. 지문은 [[지문]]...[[/지문]] 태그 사용.
            6. 정답은 [[정답]], 해설은 [[해설]] 태그 사용.
            7. 보기는 ①, ②, ③, ④, ⑤ 사용.
            """
            
            try:
                model = genai.GenerativeModel(target_model_name)
                response = model.generate_content(prompt)
                parsed_data = parse_ai_response(response.text)
                
                if parsed_data:
                    header = {'title': f"{unit} 실전 TEST", 'sub': f"{publisher} - {grade} 내신대비", 'grade': grade}
                    st.session_state.ws_pdf = create_pdf(header, parsed_data, "question")
                    st.session_state.ak_pdf = create_pdf(header, parsed_data, "answer")
                    # 완료 메시지 (성공 시에만 뜸)
                    st.success(f"✅ {len(parsed_data)}문항 출제 완료! ({target_model_name})")
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
