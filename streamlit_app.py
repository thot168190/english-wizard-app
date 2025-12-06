# --------------------------------------------------------------------------
# 3. PDF 생성 엔진 (번호 100% 보이게 완전 수정판)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
   
    # 상단 여백 확보 (헤더 공간)
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=35*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=9.5, leading=14)
    style_passage = ParagraphStyle('Passage', parent=styles['Normal'], fontName=base_font, fontSize=9, leading=13)

    # 2단 레이아웃
    col_width = 90*mm
    col_gap = 10*mm
   
    frame_l = Frame(10*mm, 15*mm, col_width, 240*mm, id='F1')
    frame_r = Frame(10*mm + col_width + col_gap, 15*mm, col_width, 240*mm, id='F2')

    def draw_page(canvas, doc):
        canvas.saveState()
       
        # [헤더 디자인] - 이그잼포유 스타일 파란색
        blue_color = colors.HexColor("#2F74B5")
       
        # 1. 왼쪽 상단 박스 (출판사/단원)
        canvas.setFillColor(blue_color)
        canvas.rect(10*mm, 280*mm, 50*mm, 10*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(bold_font, 10)
        canvas.drawCentredString(35*mm, 283*mm, f"{header_info['publisher']} {header_info['unit']}")
       
        # 2. 그 아래 학년 바
        canvas.setFillColor(colors.lightgrey)
        canvas.rect(10*mm, 274*mm, 50*mm, 6*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.setFont(bold_font, 9)
        canvas.drawCentredString(35*mm, 276*mm, header_info['grade'])
       
        # 3. 우측 타이틀 (예상문제 1회)
        canvas.setFillColor(blue_color)
        canvas.setFont(bold_font, 16)
        canvas.drawRightString(200*mm, 280*mm, header_info['title'])
       
        # 4. 헤더 구분선
        canvas.setStrokeColor(blue_color)
        canvas.setLineWidth(1.5)
        canvas.line(10*mm, 270*mm, 200*mm, 270*mm)
       
        # 5. 가운데 절취선 (점선)
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.5)
        canvas.setDash(2, 2)
        mid_x = 105*mm
        canvas.line(mid_x, 15*mm, mid_x, 260*mm)
       
        # 6. 하단 로고 & 페이지
        canvas.setDash(1, 0)
        canvas.setFillColor(colors.black)
        canvas.setFont(base_font, 9)
        page_num = doc.page
        canvas.drawCentredString(A4[0]/2, 8*mm, f"- {page_num} -")
       
        canvas.setFillColor(colors.HexColor("#469C36"))
        canvas.setFont(bold_font, 9)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
       
        canvas.restoreState()

    doc.addPageTemplates([
        PageTemplate(id='TwoCol', frames=[frame_l, frame_r], onPage=draw_page),
    ])
    story = []

    for idx, item in enumerate(items_data):
       
        # ----------------------------------------------------
        # 오른쪽 칸 (문제 내용) 구성
        # ----------------------------------------------------
        content_elements = []
       
        # 1. 지문 박스
        if doc_type == "question" and item.get('passage'):
            p_pass = Paragraph(item['passage'].replace("\n", "<br/>"), style_passage)
            t_pass = Table([[p_pass]], colWidths=[80*mm])
            t_pass.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            content_elements.append(t_pass)
            content_elements.append(Spacer(1, 3*mm))

        # 2. 질문 텍스트
        q_text = item['question']
        p_question = Paragraph(q_text.replace("\n", "<br/>"), style_normal)
        content_elements.append(p_question)
        content_elements.append(Spacer(1, 2*mm))

        # 3. 보기 텍스트
        if doc_type == "question" and item.get('choices'):
            choices_html = "<br/>".join([f"&nbsp;&nbsp;{c}" for c in item['choices']])
            p_choices = Paragraph(choices_html, style_normal)
            content_elements.append(p_choices)

        # 정답지일 경우 정답+해설 추가
        if doc_type == "answer":
            if item.get('answer'):
                ans = f"<b>정답: {item['answer']}</b>"
                if item.get('explanation'):
                    ans += f"<br/><br/>해설: {item['explanation']}"
                p_ans = Paragraph(ans, style_normal)
                content_elements.append(Spacer(1, 4*mm))
                content_elements.append(p_ans)

        # ----------------------------------------------------
        # 왼쪽 칸 (문항 번호) – 완전 수정판 (절대 안 잘림!)
        # ----------------------------------------------------
        if doc_type == "question":
            num_html = f"<font name='{bold_font}' color='#2F74B5' size='15'><b>{idx+1}</b></font><font size='10' color='#2F74B5'>●</font>"
        else:
            num_html = f"<font name='{bold_font}' size='13'><b>{idx+1}</b></font>"

        p_num = Paragraph(num_html + "  ", style_normal)  # 공백으로 살짝 띄우기

        # ----------------------------------------------------
        # 메인 테이블 조립: [번호] | [내용]
        # ----------------------------------------------------
        row_data = [[p_num, content_elements]]

        t_main = Table(row_data, colWidths=[12*mm, 78*mm])  # 12 + 78 = 90mm
        t_main.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,0), 'RIGHT'),           # 번호 오른쪽 정렬
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (0,0), (0,0), 1),
            ('LEFTPADDING', (1,0), (1,-1), 4),          # 내용 왼쪽 여백
            ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F5F9FF")),  # 번호 배경 아주 연한 파랑
            ('BOX', (0,0), (0,0), 0.5, colors.HexColor("#2F74B5")),   # 번호 칸 테두리 파랑
        ]))

        story.append(KeepTogether(t_main))
        story.append(Spacer(1, 7*mm))  # 문제 간 간격 (조절 가능)

    doc.build(story)
    buffer.seek(0)
    return buffer
