import os
import streamlit as st
import time
from rag_module import create_rag_chain

st.set_page_config(page_title="주식 레포트 분석", layout="wide")

st.title("💰주식 레포트 분석")
st.markdown("업로드한 문서에 대해 질문해 보세요.")

# 캐시 적용 RAG 체인 초기화 속도 개선
@st.cache_resource(show_spinner=True)
def get_rag_chain_cached(pdf_path, chunk_size, chunk_overlap, top_k):
    return create_rag_chain(pdf_path, chunk_size, chunk_overlap, top_k)

if "messages" not in st.session_state :
    st.session_state.messages = []

if "chat_history" not in st.session_state :
    st.session_state.chat_history = []

# 1. 사이드바: 파일 업로드 및 가공
with st.sidebar:
    st.header("⚙️ 설정")
    uploaded_file = st.file_uploader("PDF 업로드", type=['pdf'])

    # 청크 사이즈, 오버랩 및 유사도 설정
    chunk_size = st.number_input(
        "문서 덩어리 크기 설정",
        min_value=300,
        max_value=2000,
        value=1000,
        step=50,
        )

    chunk_overlap = st.number_input(
        "청크 오버랩",
        min_value = 0,
        max_value = 500,
        value = 200,
        step = 50
    )

    top_k = st.number_input(
        "검색 유사도 (k)",
        min_value = 1,
        max_value = 10,
        value = 5
    )

    if st.button("초기화") :
        st.session_state.clear()
        st.rerun()

# 2. 파일 업로드 시 RAG 체인 초기화
if uploaded_file:
    # 파일을 로컬에 임시 저장
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

        # 사이드 바에서 설정한 값 수정
        current_config = (
            chunk_size,
            chunk_overlap,
            top_k,
            uploaded_file.name
        )

    # 세션 상태를 사용하여 체인을 한 번만 생성 (성능 최적화)
    if (
        "config" not in st.session_state
        or st.session_state.config != current_config
    ):

        with st.spinner("문서 분석 중..."):

            if os.path.exists(temp_path):
                st.session_state.rag_chain = get_rag_chain_cached(temp_path, chunk_size, chunk_overlap, top_k)
            else:
                st.warning("PDF 파일을 먼저 업로드해주세요.")
                st.stop()

        st.session_state.config = current_config
        st.success("분석 완료!")

    # 메시지 저장
    # if "messages" not in st.session_state :
    #     st.session_state.messages = []

    # 기존 메시지 출력
    for message in st.session_state.messages :
        with st.chat_message(message["role"]) :
            st.markdown(message["content"])

            # 출처 표시
            if "sources" in message :
                st.caption(message["sources"])

    # 사용자 입력 처리
    if prompt := st.chat_input("질문 입력") :
        
        st.session_state.messages.append({
            "role" : "user",
            "content" : prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("답변 중..."):
                start_time = time.time()
                response = st.session_state.rag_chain(prompt, st.session_state.chat_history)
                end_time = time.time()
                elapsed_time = end_time - start_time

                answer = response["answer"]
                sources = response["sources"]
                # suggestions = response["suggestions"]
                context = response["context"]
                scores = response["scores"]

                st.markdown(answer)
                st.caption(sources)
                st.caption(f"🕐 응답 시간 :  {elapsed_time : .2f}초")
                # st.markdown("💡 예상 질문")
                # for q in suggestions :
                #     st.markdown(f"- {q}")
                with st.expander("📊 검색 유사도 보기") :
                    st.text(scores)
                with st.expander("📄 검색된 문서보기") :
                    st.text(context[:3000])

        # 대화 저장
        st.session_state.messages.append({
            "role" : "assistant",
            "content" : answer,
            "sources" : sources
        })

        st.session_state.chat_history.append((prompt, answer))

else:
    st.info("분석 레포트 업로드 하세요.")