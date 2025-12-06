import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import json
import re
import os
import math

# 1. 페이지 설정
st.set_page_config(page_title="AI 문제 생성기", page_icon="📝")
st.title("📝 학원용 AI 문제 생성기 (박스+2단 편집)")

# ==========================================
# [기능] 학원 스타일 PDF 생성 함수 (최종 수정본)
# ==========================================
def create_academy_style_pdf(data_json, title_text="English Grammar Test"):
    # 1. PDF 객체 생성 (A4 세로)
    pdf = FPDF()
    pdf.add_page()
    
    # 2. 폰트 등록
    font_path = 'fonts/NotoSansKR-Regular.ttf' 
    if not os.path.exists(font_path):
        st.error(f"폰트 파일을 찾을 수 없습니다. (경로: {os.getcwd()}/{font_path})")
        return None

    try:
        pdf.add_font('NotoSansKR', '', font_path, uni=True)
    except Exception as e:
        st.error(f"폰트 등록 에러: {e}")
        return None

    # 3. 헤더 디자인
    pdf.set_font('NotoSansKR', '', 20)
    pdf.cell(0, 15, title_text, align='C', ln=True)
    
    pdf.set_font('NotoSansKR', '', 11)
    header_info = "Class: __________   Name: __________   Score: ______ / 100"
    pdf.cell(0, 10, header_info, align='R', ln=True)
    
    pdf.set_line_width(0.5)
    pdf.line(10, 35, 200, 35)
    pdf.ln(5)

    # 4. [New] 지문 박스 그리기 (회색 배경)
    passage_text = data_json.get('passage', '지문 내용이 없습니다.')
    
    pdf.set_fill_color(240, 240, 240) # 연한 회색 설정
    pdf.set_font('NotoSansKR', '', 10)
    
    # 지문 출력 (fill=True 옵션이 핵심)
    pdf.multi_cell(0, 8, txt=passage_text, border=1, fill=True)
    pdf.ln(10)

    # 5. [New] 문제 2단 편집 로직
    quiz_data = data_json.get('questions', [])
    pdf.set_font('NotoSansKR', '', 11)
    
    total_q = len(quiz_data)
    half_q = math.ceil(total_q / 2) # 절반 계산
    
    start_y = pdf.get_y() # 지문 박스 끝난 위치
    left_margin = 10
    right_margin_start = 110
    line_height = 8
    
    # 왼쪽 단 출력
    pdf.set_xy(left_margin, start_y)
    for i in range(half_q):
        item = quiz_data[i]
        question_text = f"{i+1}. {item['question']}"
        pdf.multi_cell(w=90, h=line_height, txt=question_text)
        if 'options' in item:
            for opt in item['options']:
                pdf.set_x(left_margin + 5)
                pdf.multi_cell(w=85, h=6, txt=opt)
        pdf.ln(4)

    # 오른쪽 단 출력
    pdf.set_xy(right_margin_start, start_y)
    for i in range(half_q, total_q):
        item = quiz_data[i]
        question_text = f"{i+1}. {item['question']}"
        pdf.multi_cell(w=90, h=line_height, txt=question_text)
        if 'options' in item:
            for opt in item['options']:
                pdf.set_x(right_margin_start + 5)
                pdf.multi_cell(w=85, h=6, txt=opt)
        pdf.ln(4)

    # 6. 정답 및 해설
    pdf.add_page()
    pdf.set_font('NotoSansKR', '', 14)
    pdf.cell(0, 10, "[ 정답 및 해설 ]", ln=True)
    pdf.set_font('NotoSansKR', '', 10)
    
    for i, item in enumerate(quiz_data):
        ans = item.get('answer', 'N/A')
        exp = item.get('explanation', '')
        pdf.multi_cell(0, 8, txt=f"{i+1}번 정답: {ans}\n해설: {exp}")
        pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 메인 화면 로직
# ==========================================

with st.sidebar:
    api_key = st.text_input("Google API Key를 입력하세요", type="password")

tab1, tab2 = st.tabs(["교과서 정보 입력", "지문 직접 입력"])

grade = ""
textbook = ""
unit = ""
txt_input = ""

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        grade = st.selectbox("학년", ["1학년", "2학년", "3학년"], index=0)
    with col2:
        textbook = st.text_input("교과서/출판사 (예: 동아 윤정미)", value="")
    unit = st.text_input("단원/제재 (예: Lesson 1)", value="")

with tab2:
    txt_input = st.text_area("지문을 직접 입력하세요", height=150)

generate_btn = st.button("문제 생성하기")

if generate_btn:
    if not api_key:
        st.error("🚨 구글 API 키가 필요합니다.")
        st.stop()
    
    genai.configure(api_key=api_key)
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("1/3 단계: AI가 분석 중... 🧐")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        context_prompt = ""
        if not txt_input:
            if not (grade and textbook and unit):
                st.warning("교과서 정보를 입력하거나 지문을 입력해주세요.")
                st.stop()
            context_prompt = f"중학교 {grade} {textbook} 교과서의 {unit} 본문 내용을 기반으로"
        else:
            context_prompt = f"아래 지문을 기반으로:\n{txt_input}\n"

        # [New] 프롬프트: 밑줄 대신 (A) 사용 요청
        final_prompt = f"""
        {context_prompt}
        
        다음 조건에 맞춰 중학교 {grade if grade else '중학생'} 수준의 영어 내용 일치 문제를 3개 만들어줘.
        
        [중요 조건]
        1. 지칭 추론이나 문맥상 의미를 묻는 문제를 낼 경우, **지문에 밑줄을 긋는 대신 해당 부분에 (A), (B), (C) 와 같이 표시**를 해줘.
        2. 질문에서는 "밑줄 친 부분"이라는 말 대신 "Part (A)" 와 같이 언급해줘.
        3. 반드시 (A), (B) 표시가 포함된 **지문 전체(passage)**를 JSON 결과에 포함해줘.
        
        [출력 형식]
        반드시 아래 JSON 형식만 출력해.
        
        {{
            "passage": "여기에 (A), (B) 표시가 포함된 지문 전체 내용",
            "questions": [
                {{
                    "question": "문제 질문",
                    "options": ["(a) 보기1", "(b) 보기2", "(c) 보기3", "(d) 보기4", "(e) 보기5"],
                    "answer": "정답",
                    "explanation": "해설"
                }}
            ]
        }}
        """
        
        status_text.text("2/3 단계: AI가 문제 출제 중... 🧠")
        progress_bar.progress(50)

        response = model.generate_content(final_prompt)
        text_response = response.text
        
        # JSON 정제
        clean_json_text = re.sub(r'```json\s*|\s*```', '', text_response)
        data_json = json.loads(clean_json_text)
        
        progress_bar.progress(100)
        status_text.text("생성 완료! 🎉")
        
        st.markdown("### 📜 지문 미리보기")
        st.info(data_json.get('passage', '')) 
        
        st.markdown("### 📄 생성된 문제")
        for idx, q in enumerate(data_json.get('questions', [])):
            st.markdown(f"**{idx+1}. {q['question']}**")
            for opt in q['options']:
                st.text(opt)
            with st.expander(f"정답 확인 ({idx+1}번)"):
                st.write(f"정답: {q['answer']}")
                st.write(f"해설: {q['explanation']}")
            st.markdown("---")
            
        # PDF 다운로드
        st.markdown("### 🖨️ 시험지 인쇄")
        pdf_bytes = create_academy_style_pdf(data_json, title_text=f"{unit} Review Test" if unit else "English Test")
        
        if pdf_bytes:
            st.download_button(
                label="📥 PDF 시험지 다운로드 (최종 완성본)",
                data=pdf_bytes,
                file_name="academy_test_final.pdf",
                mime="application/pdf"
            )

    except json.JSONDecodeError:
        st.error("AI 응답 형식 오류입니다. 다시 시도해주세요.")
    except Exception as e:
        st.error(f"에러가 발생했습니다: {e}")
