import os
import hashlib
import logging
import warnings
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate


warnings.filterwarnings("ignore", category=FutureWarning)
# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 캐시 폴더 생성
os.makedirs("./vector_cache", exist_ok=True)

# 임베딩 모델 수정
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def create_rag_chain(pdf_path, chunk_size = 800, chunk_overlap = 200, top_k = 3):
    try:
        # 파일 해시 생성
        with open(pdf_path, 'rb') as f:
            file_content = f.read()

        hash_input = file_content + EMBEDDING_MODEL_NAME.encode()
        file_hash = hashlib.md5(hash_input).hexdigest()
        cache_path = f"./vector_cache/{file_hash}"

        embeddings = HuggingFaceEmbeddings(model_name = EMBEDDING_MODEL_NAME)

        # 벡터 DB 로드 or 생성
        if os.path.exists(cache_path):
            logging.info("기존 벡터 DB 로드")
            vectorstore = FAISS.load_local(cache_path, embeddings, allow_dangerous_deserialization=True)
        else:
            logging.info("새 벡터 DB 생성")

            # pdf 로드
            loader = PyMuPDFLoader(pdf_path)
            docs = loader.load()

            # 청킹
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            split_documents = text_splitter.split_documents(docs)

            # 벡터 DB 생성
            vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)

            # 저장
            vectorstore.save_local(cache_path)

        # 검색기 생성
        # retriever = vectorstore.as_retriever(search_type="similarity",
        #                                      search_kwargs={"score_threshold" : 0.5, "k" : top_k})
        llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0)

        # prompt 지침
        template = """당신은 투자 리포트 분석 AI 입니다. 다음 문서 내용을 기반으로만 답변하세요.

                [문서 내용]
                {context}
                
                규칙 : 
                1. 제공된 문서 내용만 기반으로 답변하세요.
                2. 문서에 없는 내용은 추측하지 마세요.
                3. 답변은 한국어로 작성하세요.
                4. 핵심 내용을 간결하게 요약하세요.

                질문 : {question}
                답변 : """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm | (lambda x : x.content)

        # 실행 함수
        def run_rag(question, chat_history = []) : 
            score_text= ""
            context_text = ""
            source_pages = []
            docs = []

            query_embedding = embeddings.embed_query(question)

            docs_with_scores = vectorstore.similarity_search_with_score_by_vector(query_embedding, k = top_k) 

            for doc, score in docs_with_scores:
                docs.append(doc)
                page = doc.metadata.get("page", 0)
                source_pages.append(page + 1)

                score_text += (f"페이지 {page + 1}"
                               f"(유사도 점수 : {score:.4f})\n")
                context_text += (f"\n[페이지 {page + 1}]\n"
                                 f"{doc.page_content}\n")
                
            #이전 대화
            history_text = ""

            for q, a in chat_history :
                history_text += (f"\n사용자 : {q}\n"
                                 f"AI : {a}\n")
            
            # LLM 답변 생성
            llm_result = chain.invoke({"context": context_text, "question": question})

            answer_text = llm_result
            
            # 혹시라도 리스트 형태가 튀어나온다면 처리
            if isinstance(answer_text, list):
                answer_text = answer_text[0]
            
            # 딕셔너리 구조가 섞여있을 경우를 대비한 최후의 방어
            if isinstance(answer_text, dict):
                answer_text = answer_text.get('text', str(answer_text))

            # 출처 페이지
            unique_pages = sorted(list(set(source_pages)))

            source_text = ( "출처 페이지 : " + ", ".join(map(str, unique_pages)))

            # 예상 질문 생성
            # suggestion_prompt = f"""
            # 다음 문서 내용을 보고 사용자가 추가로 궁금해할 만한 질문 3개를 생성하세요.

            # 문서 : {context_text}

            # 현재 질문 : {question}

            # 조건 : 
            #  - 짧고 자연스럽게
            #  - 중복 없이
            #  - 한국어
            #  """

            # suggestion_response = llm.invoke(suggestion_prompt)

            # suggestions = suggestion_response.content.split("\n")
            # suggestions = [
            #     s.replace("-", "").strip()
            #     for s in suggestions
            #     if s.strip()
            # ][:3]

            return {
                "answer" : answer_text,
                "sources" : source_text,
                # "suggestions" : suggestions,
                "context" : context_text,
                "scores" : score_text
            }
            
        return run_rag
        
    # 예외 처리
    except Exception as e :
        logging.error(f"RAG 생성 오류 : {str(e)}")
        raise Exception(f"RAG 시스템 오류 : {str(e)}")