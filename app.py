import streamlit as st
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="AI 문제 생성기", page_icon="📝")

st.title("📝 AI 교과서 내용 일치 문제 생성기")

# 2. 사이드바: API 키 입력
with st.sidebar:
    api_key = st.text_input("Google API Key를 입력하세요", type="password")
    st.markdown("---")
    st.markdown("API 키가 없다면 [Google AI Studio](https://aistudio.google.com/)에서 발급받으세요.")

# 3. 사용자 입력 받기
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
    unit = st.text_input("단원/제재 (예: Lesson 1. The Art of Communication)", value="")

with tab2:
    txt_input = st.text_area("지문을 직접 입력하세요 (이 경우 교과서 정보는 무시됩니다)", height=150)

# 생성 버튼
generate_btn = st.button("문제 생성하기")

# 4. 로직 실행 (스크린샷에 있던 부분 + 수정된 모델)
if generate_btn:
    # (39행~41행 로직) API 키 확인
    if not api_key:
        st.error("🚨 구글 API 키가 필요합니다. 사이드바에 키를 입력해주세요.")
        st.stop()
    
    # API 설정 (코드에 누락되었을 수 있어 추가함)
    genai.configure(api_key=api_key)

    full_result = ""
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("1/3 단계: AI가 내용 일치 문제를 만드는 중... 🧐")

    # (47행~52행 로직) *** [수정 완료] 최신 모델인 gemini-1.5-flash 사용 ***
    try:
        # 구버전 'gemini-pro' 대신 최신 모델 사용
        model = genai.GenerativeModel('gemini-1.5-flash') 
    except Exception as e:
        st.error(f"모델 설정 오류: {e}")
        st.stop()

    # (54행~58행 로직) 프롬프트 맥락 설정
    context_prompt = ""
    if not txt_input:
        # 지문 입력이 없으면 교과서 정보 사용
        if not (grade and textbook and unit):
            st.warning("교과서 정보를 모두 입력하거나 지문을 입력해주세요.")
            st.stop()
        context_prompt = f"중학교 {grade} {textbook} 교과서의 {unit} 본문 전체 내용을 기반으로"
    else:
        # 지문 입력이 있으면 지문 사용
        context_prompt = f"아래 입력된 지문을 기반으로:\n{txt_input}\n"

    # --- 이후 실제 생성 요청 로직 (스크린샷 이후 내용 추정 및 구현) ---
    
    # 실제 AI에게 보낼 최종 프롬프트 구성
    final_prompt = f"""
    {context_prompt}
    
    다음 조건에 맞춰 영어 내용 일치 문제를 3문제 만들어줘.
    
    [조건]
    1. 5지 선다형 객관식 문제로 만들 것.
    2. 질문은 영어로, 보기도 영어로 작성할 것.
    3. 정답과 해설은 한국어로 맨 아래에 따로 표시할 것.
    4. 학생 수준은 중학교 {grade if grade else '중학생'} 수준에 맞출 것.
    """

    try:
        # 콘텐츠 생성 요청
        response = model.generate_content(final_prompt)
        
        progress_bar.progress(100)
        status_text.text("생성 완료! 🎉")
        
        st.markdown("### 📄 생성된 문제")
        st.markdown(response.text)
        
    except Exception as e:
        st.error(f"에러가 발생했습니다: {e}")