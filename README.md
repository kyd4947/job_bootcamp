💰 주식 레포트 분석 AI (RAG System)
이 프로젝트는 사용자가 업로드한 PDF 형식의 주식 리포트를 Google Gemini AI와 RAG(Retrieval-Augmented Generation) 기술을 활용하여 분석하고, 관련 질문에 대한 답변을 제공하는 AI 웹 서비스입니다.

🚀 주요 기능
PDF 문서 분석: 업로드된 주식 리포트 PDF를 텍스트로 추출 및 임베딩.

지능형 질의응답: RAG 기술을 통해 문서 내 정확한 정보를 바탕으로 답변 생성.

상세 정보 확인: 답변의 출처, 검색 유사도(Score), 참조한 문서 조각(Context) 확인 가능.

사용자 맞춤 설정: 문서 분석을 위한 청크 사이즈, 오버랩, 검색 개수(k) 설정 기능.

🛠 사용 기술
Language: Python 3.10
Framework: Streamlit (웹 인터페이스)
AI Model: Google Gemini (LangChain 기반)
Database: ChromaDB (로컬 벡터 저장소)
Deployment: Streamlit Community Cloud

⚙️ 설정 방법 (로컬 실행 시)
환경 변수 설정: 프로젝트 루트 폴더에 .env 파일을 만들고 API 키를 입력하세요.

Plaintext
GOOGLE_API_KEY=your_gemini_api_key_here
라이브러리 설치:

Bash
pip install -r requirements.txt
실행:

Bash
streamlit run app.py

📋 프로젝트 구조
app.py: 웹 화면 구성 및 전체 흐름 제어.
rag_module.py: PDF 로드, 임베딩, 벡터 저장소 및 RAG 체인 생성 로직.
requirements.txt: 프로젝트 의존성 목록.

💡 참고사항
본 서비스는 PDF 파일을 업로드하면 temp_ 파일로 임시 저장하여 분석을 수행합니다.
분석 속도 개선을 위해 @st.cache_resource를 활용한 캐싱 기능을 적용하였습니다.
