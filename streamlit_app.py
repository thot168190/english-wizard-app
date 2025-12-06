# --------------------------------------------------------------------------
# 3. PDF 생성 엔진 – 완전 최종판 (2단에서도 절대 안 깨짐, 번호 안 잘림)
# --------------------------------------------------------------------------
def create_pdf(header_info, items_data, doc_type="question"):
    buffer = BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=35*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=base_font, fontSize=9.8, leading=14)
    style_passage = ParagraphStyle('Passage', parent=styles['Normal'], fontName=base_font, fontSize=9.2, leading=13.5)

    col_width = 90*mm
    col_gap = 10*mm
    frame_l = Frame(10*mm, 15*mm, col_width, 240*mm, id='left')
    frame_r = Frame(120*mm, 15*mm, col_width, 240*mm, id='right')

    def _on_page(canvas, doc):
        blue = colors.HexColor("#2F74B5")
        canvas.saveState()
        canvas.setFillColor(blue)
        canvas.rect(10*mm, 280*mm, 50*mm, 10*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(bold_font, 10.5)
        canvas.drawCentredString(35*mm, 283*mm, f"{header_info['publisher']} {header_info['unit']}")
        
        canvas.setFillColor(colors.lightgrey)
        canvas.rect(10*mm, 274*mm, 50*mm, 6*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.black)
        canvas.setFont(bold_font, 9)
        canvas.drawCentredString(35*mm, 276*mm, header_info['grade'])
        
        canvas.setFillColor(blue)
        canvas.setFont(bold_font, 16)
        canvas.drawRightString(200*mm, 280*mm, header_info['title'])
        
        canvas.setStrokeColor(blue)
        canvas.setLineWidth(1.8)
        canvas.line(10*mm, 270*mm, 200*mm, 270*mm)
        
        canvas.setStrokeColor(colors.grey)
        canvas.setDash(3,3)
        canvas.line(105*mm, 15*mm, 105*mm, 260*mm)
        
        canvas.setDash()
        canvas.setFont(base_font, 9)
        canvas.drawCentredString(A4[0]/2, 8*mm, f"- {doc.page} -")
        canvas.setFillColor(colors.HexColor("#469C36"))
        canvas.setFont(bold_font, 9.5)
        canvas.drawRightString(200*mm, 8*mm, "엠베스트 SE 광사드림 학원")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame_l, frame_r], onPage=_on_page)])
    story = []

    for idx, item in enumerate(items_data):
        # ---------- 번호 ----------
        if doc_type == "question":
            num_text = f"<font name='{bold_font}' color='#2F74B5' size='16'><b>{idx+1}</b></font><font size='11' color='#2F74B5'>●</font>"
        else:
            num_text = f"<font name='{bold_font}' size='13'><b>{idx+1}</b></font>"
        p_num = Paragraph(num_text + "   ", style_normal)

        # ---------- 내용 ----------
        elements = []

        # 지문
        if doc_type == "question" and item.get('passage'):
            passage = item['passage'].replace("\n", "<br/>")
            p = Paragraph(passage, style_passage)
            t = Table([[p]], colWidths=[76*mm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f9fa")),
                ('BOX', (0,0), (-1,-1), 0.8, colors.grey),
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
                ('PADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 4*mm))

        # 질문
        q = item['question'].replace("\n", "<br/>")
        elements.append(Paragraph(q, style_normal))
        elements.append(Spacer(1, 3*mm))

        # 보기
        if doc_type == "question" and item.get('choices'):
            choices = "<br/>".join(f"　{c}" for c in item['choices'])
            elements.append(Paragraph(choices, style_normal))

        # 정답지 해설
        if doc_type == "answer":
            if item.get('answer'):
                ans = f"<b>정답: {item['answer']}</b>"
                if item.get('explanation'):
                    ans += f"<br/><br/>해설: {item['explanation']}"
                elements.append(Spacer(1, 5*mm))
                elements.append(Paragraph(ans, style_normal))

        # ---------- 한 문제 전체 테이블 (이게 핵심! 깨지지 않게 강제 고정) ----------
        data = [[p_num, elements]]
        table = Table(data, colWidths=[14*mm, 76*mm])   # ← 여기만 잘 잡으면 절대 안 깨짐
        table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,0), 'RIGHT'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (0,0), (0,0), 2),
            ('LEFTPADDING', (1,0), (1,-1), 5),
            ('BACKGROUND', (0,0), (0,0), colors.HexColor("#f0f4ff")),
            ('BOX', (0,0), (0,0), 1, colors.HexColor("#2F74B5")),
        ]))
        
        # ← 이 한 줄이 제일 중요! 2단에서 Frame 넘칠 때도 안전하게 처리
        story.append(KeepInFrame(maxWidth=0, maxHeight=0, content=[table, Spacer(1, 8*mm)]))

    doc.build(story)
    buffer.seek(0)
    return buffer
