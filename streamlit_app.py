from fpdf import FPDF
import math

def create_academy_style_pdf(quiz_data):
    # 1. PDF 객체 생성 (A4 세로)
    pdf = FPDF()
    pdf.add_page()
    
    # 2. 폰트 등록 (아까 성공한 그 경로!)
    font_path = 'fonts/NotoSansKR-Regular.ttf'
    pdf.add_font('NotoSansKR', '', font_path, uni=True)
    pdf.set_font('NotoSansKR', '', 10)

    # ==========================================
    # [디자인 1] 학원 스타일 헤더 (제목 + 점수칸)
    # ==========================================
    
    # 상단 타이틀 (중앙 정렬, 크게)
    pdf.set_font('NotoSansKR', '', 20)
    pdf.cell(0, 15, "English Grammar Test", align='C', ln=True)
    
    # 반, 이름, 점수 칸 (오른쪽 정렬)
    pdf.set_font('NotoSansKR', '', 11)
    # 공백을 둬서 밑줄 긋기 편하게 만듦
    header_info = "Class: __________   Name: __________   Score: ______ / 100"
    pdf.cell(0, 10, header_info, align='R', ln=True)
    
    # 구분선 (이중선 느낌을 위해 굵은 선 하나)
    pdf.set_line_width(0.5)
    pdf.line(10, 35, 200, 35) # (x1, y1) -> (x2, y2)
    pdf.ln(10) # 줄바꿈

    # ==========================================
    # [디자인 2] 2단 편집 (왼쪽 단 -> 오른쪽 단)
    # ==========================================
    
    pdf.set_font('NotoSansKR', '', 11)
    
    # 문제 개수 계산
    total_q = len(quiz_data)
    half_q = math.ceil(total_q / 2) # 절반 지점 계산 (홀수면 왼쪽이 하나 더 많음)
    
    # 시작 좌표 설정
    start_y = pdf.get_y() # 헤더 바로 아래 위치 기억
    left_margin = 10
    right_margin_start = 110 # 오른쪽 단 시작 위치 (A4 폭이 210이므로 중간쯤)
    line_height = 8 # 줄 간격
    
    # --- 왼쪽 단 출력 (1번 ~ 절반) ---
    pdf.set_xy(left_margin, start_y)
    
    for i in range(half_q):
        item = quiz_data[i]
        question_text = f"{i+1}. {item['question']}"
        
        # 문제 출력 (Multi_cell은 자동 줄바꿈 됨)
        # 폭(w)을 90으로 줘서 왼쪽 단 안벗어나게 함
        pdf.multi_cell(w=90, h=line_height, txt=question_text)
        
        # 보기 출력 (4지선다 예시) - 보기가 있다면 주석 해제해서 쓰세요
        # for option in item['options']:
        #     pdf.set_x(left_margin + 5) # 들여쓰기
        #     pdf.cell(90, line_height, txt=option, ln=True)
            
        pdf.ln(2) # 문제 사이 약간의 공백

    # --- 오른쪽 단 출력 (절반 이후 ~ 끝) ---
    # y좌표를 다시 맨 위(start_y)로 올림
    max_y_left = pdf.get_y() # 왼쪽 단이 끝난 위치 기억 (나중에 페이지 넘길 때 필요할 수 있음)
    pdf.set_xy(right_margin_start, start_y)
    
    for i in range(half_q, total_q):
        item = quiz_data[i]
        question_text = f"{i+1}. {item['question']}"
        
        pdf.multi_cell(w=90, h=line_height, txt=question_text)
        
        # 보기 출력 (4지선다 예시)
        # for option in item['options']:
        #     pdf.set_x(right_margin_start + 5)
        #     pdf.cell(90, line_height, txt=option, ln=True)
            
        pdf.ln(2)

    # 3. PDF 바이트로 변환
    return pdf.output(dest='S').encode('latin-1')
