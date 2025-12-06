import streamlit as st
import google.generativeai as genai
from weasyprint import HTML
from io import BytesIO

st.set_page_config(page_title="엠베스트 SE 광사드림 학원", page_icon="Trophy", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown("<h1 style='text-align:center; color:#1E40AF;'>엠베스트 SE 광사드림 학원</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#374151;'>AI 교과서 맞춤 문제지 생성기</h2>", unsafe_allow_html=True)
st.markdown("---")

grade = st.selectbox("학년", ["중1", "중2", "중3", "고1", "고2", "고3"])
if grade == "중1":
    publisher = "동아 (윤정미)"
elif grade == "중2":
    publisher = st.selectbox("출판사", ["천재 (정사열)", "천재 (이재영)", "비상 (김진완)"])
else:
    publisher = "공통 교과서"

units = ["1. Nice to Meet You", "2. Art Around Us", "3. Life in the Future", "4. Travel", "5. Science", "6. Culture", "7. Global Issues", "8. Success"]
unit = st.selectbox("단원 선택", units)

num_questions = st.slider("문제 수", 10, 50,30,step=5)

if st.button("PDF 문제지 + 해답지 생성 (한글 완벽)", type="primary", use_container_width=True):
    with st.spinner("엠베스트 전용 문제지 만드는 중..."):
        prompt = f"""
        엠베스트 SE 광사드림 학원 전용 문제지
        {grade} {publisher} {unit} 단원, 총 {num_questions}문항
        학교 시험지처럼 위아래 여백 넉넉하고 보기 정렬 깔끔하게
        출력 형식:

        ===문제지===
        1. 문제 내용
           ① 보기1  ② 보기2  ③ 보기3  ④ 보기4

        ===해답지===
        1. 정답: ②  해설: ...
        """
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw = response.text

        parts = raw.split("===해답지===")
        worksheet = parts[0].replace("===문제지===", "").strip()
        answerkey = parts[1].strip() if len(parts) > 1 else ""

        # HTML로 PDF 생성 (한글 100% 완벽)
        def html_to_pdf(html_content, title):
            html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    @page {{ size: A4; margin: 2.5cm 2cm 2.5cm 2cm; }}
                    body {{ font-family: "Malgun Gothic", sans-serif; font-size: 12pt; line-height: 1.8; }}
                    h1 {{ text-align: center; color: #1E40AF; }}
                    h2 {{ text-align: center; }}
                    .question {{ margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1>엠베스트 SE 광사드림 학원</h1>
                <h2>{title}</h2>
                <hr>
                <pre style="white-space: pre-wrap; font-family: inherit;">{html_content}</pre>
            </body>
            </html>
            """
            buffer = BytesIO()
            HTML(string=html).write_pdf(buffer)
            buffer.seek(0)
            return buffer

        ws_pdf = html_to_pdf(worksheet, f"{grade} {unit} 문법·독해 문제 ({num_questions}문항)")
        ak_pdf = html_to_pdf(answerkey, f"{grade} {unit} 정답 및 해설")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("문제지 PDF 다운로드", ws_pdf, f"엠베스트_{grade}_{unit}_문제지.pdf", "application/pdf")
        with col2:
            st.download_button("해답지 PDF 다운로드", ak_pdf, f"엠베스트_{grade}_{unit}_해답지.pdf", "application/pdf")

        st.success("완성! 한글 완벽 + 인쇄 바로 가능")
        st.balloons()
