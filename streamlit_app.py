import streamlit as st
import google.generativeai as genai
from reportlab.platypus import BaseDocTemplate, Paragraph, Frame, PageTemplate, Table, TableStyle, Spacer, KeepInFrame
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
st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="trophy", layout="wide")

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
    unit_code = unit.replace("과", "")
    file_name = f"{grade}_{pub_code}_{unit_code}과.txt"
    file_path = os.path.join("data", file_name)
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read(), True, file_name
    return "", False, file_name

# --------------------------------------------------------------------------
# 3. PDF 생성 엔진 – 완전 최종판 (2단에서도 절대 안 깨짐!)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=35*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=9.8, leading=14.5)
    style_passage = ParagraphStyle('Passage', parent=styles['Normal'], fontName=base_font, fontSize=9.3, leading=13.8)

    frame_l = Frame(10*mm, 15*mm, 90*mm, 240*mm, id='left')
    frame_r = Frame(110*mm, 15*mm, 90*mm, 240*mm, id='right')

    def draw_header(canvas, doc):
        blue = colors.HexColor("#2F74B5")
        canvas.saveState()
        canvas.setFillColor(blue)
        canvas.rect(10*mm, 280*mm, 52*mm, 10*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(bold_font, 11)
        canvas.drawCentredString(36*mm, 283*mm, f"{header_info['publisher']} {header_info['unit']}")
        
        canvas.setFillColor(colors.HexColor("#e9ecef"))
        canvas.rect(10*mm, 274*mm, 52*mm, 6*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.setFont(bold_font, 9)
        canvas.drawCentredString(36*mm, 276*mm, header_info['grade'])
        
        canvas.setFillColor(blue)
        canvas.setFont(bold_font, 17)
        canvas.drawRightString(200*mm, 280*mm, header_info['title'])
        
        canvas.setStrokeColor(blue)
        canvas.setLineWidth(2)
        canvas.line(10*mm, 270*mm, 200*mm, 270*mm)
        
        canvas.setStrokeColor(colors.HexColor("#ced4da"))
        canvas.setDash(4,3)
        canvas.line(105*mm, 15*mm, 105*mm, 260*mm)
        
        canvas.setDash()
        canvas.setFont(base_font, 9)
        canvas.drawCentredString(A4[0]/2, 8*mm, f"– {doc.page} –")
        canvas.setFillColor(colors.HexColor("#469C36"))
        canvas.setFont(bold_font, 10)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(frames=[frame_l, frame_r], onPage=draw_header)])
    story = []

    for idx, item in enumerate(items_data):
        # 번호
        if doc_type == "question":
            num_html = f"<font name='{bold_font}' color='#2F74B5' size='17'><b>{idx+1}</b></font><font size='11' color='#2F74B5'> ●</font>"
        else:
            num_html = f"<font name='{bold_font}' size='14'><b>{idx+1}</b></font>"
        p_num = Paragraph(num_html + "  ", style_normal)

        # 내용
        content = []

        # 지문
        if doc_type == "question" and item.get('passage'):
            p = Paragraph(item['passage'].replace("\n", "<br/>"), style_passage)
            t = Table([[p]], colWidths=[76*mm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f9fa")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#adb5bd")),
                ('ROUNDEDCORNERS', [8,8,8,8]),
                ('PADDING', (0,0), (-1,-1), 7),
            ]))
            content.append(t)
            content.append(Spacer(1, 4*mm))

        # 질문
        content.append(Paragraph(item['question'].replace("\n", "<br/>"), style_normal))
        content.append(Spacer(1, 3*mm))

        # 보기
        if doc_type == "question" and item.get('choices'):
            choices = "<br/>".join(f"　{c}" for c in item['choices'])
            content.append(Paragraph(choices, style_normal))

        # 정답지
        if doc_type == "answer":
            if item.get('answer'):
                ans = f"<b>정답: {item['answer']}</b>"
                if item.get('explanation'):
                    ans += f"<br/><br/>해설: {item['explanation']}"
                content.append(Spacer(1, 6*mm))
                content.append(Paragraph(ans, style_normal))

        # 핵심: KeepInFrame으로 강제 보호 → 2단에서도 절대 안 깨짐!
        main_table = Table([[p_num, content]], colWidths=[14*mm, 76*mm])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,0), 'RIGHT'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (0,0), (0,0), 3),
            ('LEFTPADDING', (1,0), (1,-1), 5),
            ('BACKGROUND', (0,0), (0,0), colors.HexColor("#e3f2fd")),
            ('BOX', (0,0), (0,0), 1.2, colors.HexColor("#1976d2")),
        ]))
        
        story.append(KeepInFrame(maxWidth=0, maxHeight=0, content=[main_table, Spacer(1, 9*mm)]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------
# 4. AI 파싱 로직
# --------------------------------------------------------------------------
def parse_ai_response(text):
    questions = []
    blocks = re.split(r'\[\[문제\]\]', text)
    if len(blocks) < 2:
        blocks = re.split(r'\n\s*\d+\.\s+', text)
        blocks = [''] + blocks

    for block in blocks[1:]:
        if not block.strip(): continue
        item = {'passage': '', 'question': '', 'choices': [], 'answer': '', 'explanation': ''}

        # 지문
        if "[[지문]]" in block and "[[/지문]]" in block:
            item['passage'] = block.split("[[지문]]")[1].split("[[/지문]]")[0].strip()
            block = block.split("[[/지문]]")[1]

        # 정답/해설
        if "[[정답]]" in block:
            parts = block.split("[[정답]]")
            content = parts[0]
            rest = parts[1]
            if "[[해설]]" in rest:
                item['answer'] = rest.split("[[해설]]")[0].strip()
                item['explanation'] = rest.split("[[해설]]")[1].strip()
            else:
                item['answer'] = rest.strip()
            block = content

        # 질문 + 보기
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        q_lines = []
        for line in lines:
            if re.match(r'^(①|②|③|④|⑤|[1-5][\.\)]|[가-하]|[A-E][\.\)])', line):
                item['choices'].append(line)
            else:
                clean = re.sub(r'^\d+[\.\)]\s*', '', line)
                if clean: q_lines.append(clean)
        item['question'] = " ".join(q_lines).strip()

        if item['question']:
            questions.append(item)
    return questions

# --------------------------------------------------------------------------
# 5. 메인 UI
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
    st.warning(f"'{file_name}' 파일이 없습니다.")
    source_text = st.text_area("직접 본문을 붙여넣으세요.", height=180)

c_opt1, c_opt2, c_opt3 = st.columns([2, 1, 1])
with c_opt1:
    q_types = st.multiselect("출제 유형", ["내용일치", "빈칸추론", "어법", "지칭추론", "순서배열", "문장삽입", "어휘"], default=["내용일치", "빈칸추론", "어법"])
with c_opt2:
    difficulty = st.select_slider("난이도", options=["하", "중", "상"], value="중")
with c_opt3:
    num_q = st.slider("문항 수", 5, 20, 10)

if st.button("시험지 생성 (Start)", type="primary", use_container_width=True):
    if not source_text.strip():
        st.error("본문이 없습니다.")
    else:
        with st.spinner("AI가 문제를 만들고 있습니다..."):
            prompt = f"""
            중학교 영어 내신 전문가로서 {grade} {publisher} {unit} 본문을 바탕으로 {num_q}문항을 출제해 주세요.
            난이도: {difficulty} / 유형: {', '.join(q_types)}

            본문:
            {source_text}

            출력 형식:
            [[문제]]
            [[지문]]...[[/지문]] (필요시)
            질문 (한국어)
            ① 보기1
            ② 보기2
            ...
            [[정답]]③
            [[해설]]해설 내용
            """
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                parsed = parse_ai_response(response.text)

                if parsed:
                    header = {
                        'publisher': publisher.split()[0],
                        'unit': unit,
                        'title': "예상문제 1회",
                        'grade': grade
                    }
                    st.session_state.ws_pdf = create_pdf(header, parsed, "question")
                    st.session_state.ak_pdf = create_pdf(header, parsed, "answer")
                    st.success(f"완성! {len(parsed)}문항 생성됨")
                else:
                    st.error("문제를 만들지 못했습니다.")
            except Exception as e:
                st.error(f"오류: {e}")

if st.session_state.ws_pdf and st.session_state.ak_pdf:
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("시험지 다운로드", st.session_state.ws_pdf, "Exam_Paper.pdf", "application/pdf", use_container_width=True)
    with c2:
        st.download_button("정답지 다운로드", st.session_state.ak_pdf, "Answer_Key.pdf", "application/pdf", use_container_width=True)

st.caption("Developed by 엠베스트 SE 광사드림 학원 – 2025")
