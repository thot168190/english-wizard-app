import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import json
import re
import os

# 1. 페이지 설정
st.set_page_config(page_title="AI 문제 생성기", page_icon="📝")
st.title("📝 학원용 AI 문제 생성기 (지문 박스형)")

# ==========================================
# [기능] 학원 스타일 PDF 생성 함수
# ==========================================
def create_academy_style_pdf(data_json, title_text="English Grammar Test"):
    # 1. PDF 객체 생성 (A4 세로)
    pdf = FPDF()
    pdf.add_page()
    
    # 2. 폰트 등록 (fonts 폴더 확인 필수)
    # 폰트 파일이 있는지 먼저 확인합니다.
    font_path = 'fonts/NotoSansKR-Regular.ttf' 
    if not os.path.exists(font_path):
        st.error(f"폰트 파일을 찾을 수 없습니다. (경로: {os.getcwd()}/{font_path})")
        return None

    try:
        pdf.add_font('NotoSansKR', '', font_path, uni=True)
    except Exception as e:
        st.error(f"폰트 등록 중 오류 발생: {e}")
        return None

    # 3. 헤더 (타이틀 + 점수칸)
    pdf.set_font('NotoSansKR', '', 20)
    pdf.cell(0, 15, title_text, align='C', ln=True)
    
    pdf.set_font('NotoSansKR', '', 11)
    header_info = "Class: __________   Name: __________   Score: ______ / 100"
    pdf.cell(0, 10, header_info, align='R', ln=True)
    
    pdf.set_line_width(0.5)
    pdf.line(10, 35, 200, 35)
    pdf.ln(5)

    # 4. 지문 박스 출력 (회색 배경)
    passage_text = data_json.get('passage', '지문 내용이 없습니다.')
    
    pdf.set_fill_color(245, 245, 245) # 아주 연한 회색
    pdf.set_font('NotoSansKR', '', 10)
    
    # 지문이 들어갈 높이 계산 (대략적으로)
    pdf.multi_cell(0, 8, txt=passage_text, border=1, fill=True)
    pdf.ln(10) # 지문과 문제 사이 간격

    # 5. 문제 2단 편집 로직
    quiz_data = data_json.get('questions', [])
    
    pdf.set_font('NotoSansKR', '', 11)
    
    total_q = len(quiz_data)
    import math
    half_q = math.ceil(total_q / 2)
    
    start_y = pdf.get_y() # 지문 박스 끝난 위치부터 시작
    left_margin = 10
    right_margin_start = 110
    line_height = 8
    
    # --- 왼쪽 단 ---
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

    # --- 오른쪽 단 ---
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

    # 6. 정답 및 해설 (다음 페이지)
    pdf.add_page()
    pdf.set_font('NotoSansKR', '', 14)
    pdf.cell(0, 10, "[ 정답 및 해설 ]", ln=True)
    pdf.set_font('NotoSansKR', '', 10)
    
    for i, item in enumerate(quiz_
