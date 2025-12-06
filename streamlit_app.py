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
# [선생님이 주신 본문 데이터]
# --------------------------------------------------------------------------
DEFAULT_TEXT = """
[Lesson 1. Who Is in Your Heart?]

I'm Jihun. My best friend is Minsu. Minsu and I love rock music. 
We are members of the school band Rock It. I play the guitar, and Minsu plays the drums. 
We are not good players, but we have so much fun together. 
With Minsu, I laugh all the time. Together, we are happy.

I'm Hannah. Mrs. Schmidt, my neighbor, is a dear friend to me. 
She is a great listener, and I often talk with her. 
She doesn't talk much. She just nods and smiles at me. 
Sometimes I'm sad, and she bakes a cake for me. 
Her cake is yummy, and I feel all right, like magic. 
With Mrs. Schmidt, I feel at home. Together, we are happy.

I'm Tim. Hope is my guide dog and my best friend. 
She is by my side 24/7. She even goes to school with me. 
Is she a good student? Well, she mostly sleeps in class, but the teachers don't mind. 
On weekends, we go to the park and play together. 
With Hope, I feel free and strong. Together, we are happy.
"""

# --------------------------------------------------------------------------
# 1. 설정 및 폰트
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

# --------------------------------------------------------------------------
# 2. PDF 생성 엔진 (문제지/정답지 공용)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=10, leading=15)
    style_box = ParagraphStyle('Box', parent=styles['Normal'], fontName=base_font, fontSize=9.5, leading=14)

    # 2단 레이아웃
    frame_w = 92*mm
    gap = 6*mm
    
    # 1페이지 (헤더 공간)
    frame_f_l = Frame(10*mm, 15*mm, frame_w, 220*mm, id='F1_L')
    frame_f_r = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 220*mm, id='F1_R')
    # 2페이지 (꽉 채움)
    frame_l_l = Frame(10*mm, 15*mm, frame_w, 260*mm, id='F2_L')
    frame_l_r = Frame(10*mm + frame_w + gap, 15*mm, frame_w, 260*mm, id='F2_R')

    # [헤더 그리기]
    def draw_first_page(canvas, doc):
        canvas.saveState()
        title = header_info['title']
        if doc_type == "answer":
            title += " [정답 및 해설]"
            
        canvas.setFont(bold_font, 18)
        canvas.drawCentredString(A4[0]/2, 280*mm, title)
        canvas.setFont(base_font, 11)
        canvas.drawCentredString(A4[0]/2, 273*mm, header_info['sub'])
        
        # 결재란 (문제지에만 표시, 정답지는 생략 가능하지만 통일성 위해 유지)
        canvas.setLineWidth(0.5)
        canvas.rect(10*mm, 255*mm, 190*mm, 12*mm)
        canvas.setFont(base_font, 10)
        canvas.drawString(15*mm, 259*mm, f"학년: {header_info['grade']}   |   이름: ________________   |   점수: __________")
        
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 250*mm)
        
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.drawCentredString(A4[0]/2, 8*mm, f"- {doc.page} -")
        canvas.restoreState()

    def draw_later_page(canvas, doc):
        canvas.saveState()
        canvas.setDash(2, 2)
        canvas.line(A4[0]/2, 15*mm, A4[0]/2, 280*mm)
        canvas.setFont(base_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.drawCentredString(A4[0]/2, 8*mm, f"- {doc.page} -")
        canvas.restoreState()

    doc.addPageTemplates([
        PageTemplate(id='First', frames=[frame_f_l, frame_f_r], onPage=draw_first_page),
        PageTemplate(id='Later', frames=[frame_l_l, frame_l_r], onPage=draw_later_page)
    ])

    story = []
    
    for idx, item in enumerate(items_data):
        # === 문제지 생성 모드 ===
        if doc_type == "question":
            # 1. 지문 박스
            if item.get('passage'):
                p = Paragraph(item['passage'].replace("\n", "<br/>"), style_box)
                t = Table([[p]], colWidths=[88*mm])
                t.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
                    ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(t)
                story.append(Spacer(1, 3*mm))
            
            # 2. 문제 본문
            num_text = f"<font color='darkblue'><b>{idx+1}.</b></font>"
            q_text = item['question']
            if item.get('choices'):
                q_text += "<br/><br/>" + "<br/>".join(item['choices'])
            
            data = [[Paragraph(num_text, style_normal), Paragraph(q_text, style_normal)]]
            t_q = Table(data, colWidths=[8*mm, 82*mm])
            t_q.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(KeepTogether([t_q, Spacer(1, 6*mm)]))
            
        # === 정답지 생성 모드 ===
        else:
            # 1. 정답 및 해설 표시
            num_text = f"<b>{idx+1}.</b>"
            ans = item.get('answer', '정답 없음')
            exp = item.get('explanation', '')
            
            # 보기 좋게 포맷팅
            content = f"<b>정답: {ans}</b><br/>"
            if exp:
                content += f"<font color='gray'>[해설]</font> {exp}"
            
            data = [[Paragraph(num_text, style_normal), Paragraph(content, style_normal)]]
            t_a = Table(data, colWidths=[8*mm, 82*mm])
            t_a.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(KeepTogether([t_a]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------
# 3. AI 파싱 로직 (정답/해설 분리)
# --------------------------------------------------------------------------
def parse_ai_response(text):
    questions = []
    # [[문제]] 태그로 분리
    blocks = text.split("[[문제]]")
    
    for block in blocks:
        if not block.strip(): continue
        
        item = {'passage': '', 'question': '', 'choices': [], 'answer': '', 'explanation': ''}
        
        # 지문 추출
        if "[[지문]]" in block and "[[/지문]]" in block:
            parts = block.split("[[/지문]]")
            passage_part = parts[0].split("[[지문]]")[1]
            item['passage'] = passage_part.strip()
            remain = parts[1]
        else:
            remain = block
            
        # 정답 및 해설 추출
        if "[[정답]]" in remain:
            parts = remain.split("[[정답]]")
            content_part = parts[0]
            ans_part = parts[1]
            
            if "[[해설]]" in ans_part:
                ans_parts = ans_part.split("[[해설]]")
                item['answer'] = ans_parts[0].strip()
                item['explanation'] = ans_parts[1].strip()
            else:
                item['answer'] = ans_part.strip()
                
            remain = content_part # 질문/보기 파싱을 위해 남은 부분
        
        # 질문/보기 파싱
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
        
        if item['question']:
            questions.append(item)
            
    return questions

# --------------------------------------------------------------------------
# 4. UI 및 실행
# --------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:#374151;'>High-Level 실전 시험지 (정답지 포함)</h3>", unsafe_allow_html=True)
st.markdown("---")

if "ws_pdf" not in st.session_state:
    st.session_state.ws_pdf = None
if "ak_pdf" not in st.session_state:
    st.session_state.ak_pdf = None

c1, c2, c3 = st.columns(3)
with c1:
    grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2"])
with c2:
    publisher = st.selectbox("출판사", ["동아 (윤정미)", "천재 (이재영)", "비상 (김진완)"])
with c3:
    unit = st.text_input("단원명", "Lesson 1")

st.markdown("##### 📝 시험 범위 본문")
source_text = st.text_area("본문 내용", value=DEFAULT_TEXT, height=200)

c_opt1, c_opt2 = st.columns(2)
with c_opt1:
    q_types = st.multiselect("유형", ["내용일치", "빈칸추론", "어법", "지칭추론", "순서배열"], default=["내용일치", "빈칸추론", "어법"])
with c_opt2:
    num_q = st.slider("문항 수", 5, 20, 10)

if st.button("시험지 및 정답지 생성 (Start)", type="primary"):
    with st.spinner("AI가 문제를 출제하고 정답을 정리 중입니다..."):
        prompt = f"""
        당신은 영어 내신 시험 출제자입니다.
        [본문]을 바탕으로 {num_q}개의 문제를 만드세요.
        
        [본문]
        {source_text}
        
        [규칙]
        1. 인삿말 금지. 바로 데이터만 출력.
        2. 각 문제는 [[문제]] 태그로 시작.
        3. 지문은 [[지문]]...[[/지문]] 태그 사용.
        4. 정답은 [[정답]], 해설은 [[해설]] 태그 사용.
        
        [출력 포맷]
        [[문제]]
        [[지문]]
        (지문 내용)
        [[/지문]]
        다음 빈칸에 들어갈 말은?
        ① apple
        ② banana
        ...
        [[정답]] ①
        [[해설]] 문맥상 사과가 맞습니다.
        
        [[문제]]
        (다음 문제...)
        """
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            
            # 파싱
            parsed_data = parse_ai_response(response.text)
            
            if parsed_data:
                header = {'title': f"{unit} 실전 TEST", 'sub': f"{publisher} - {grade} 내신대비", 'grade': grade}
                
                # 문제지 PDF 생성
                st.session_state.ws_pdf = create_pdf(header, parsed_data, doc_type="question")
                # 정답지 PDF 생성
                st.session_state.ak_pdf = create_pdf(header, parsed_data, doc_type="answer")
                
                st.success(f"✅ 총 {len(parsed_data)}문항 생성 완료! 아래에서 다운로드하세요.")
            else:
                st.error("AI 응답을 분석하지 못했습니다.")
                
        except Exception as e:
            st.error(f"오류: {e}")

# 다운로드 버튼 영역
if st.session_state.ws_pdf and st.session_state.ak_pdf:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button("📄 문제지 다운로드", st.session_state.ws_pdf, "Exam_Paper.pdf", "application/pdf", use_container_width=True)
    with col_d2:
        st.download_button("🔑 정답지 다운로드", st.session_state.ak_pdf, "Answer_Key.pdf", "application/pdf", use_container_width=True)

st.markdown("---")
st.caption("Developed by 엠베스트 SE 광사드림 학원")
