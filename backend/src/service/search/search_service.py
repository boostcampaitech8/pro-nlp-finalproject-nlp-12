from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.runnables import RunnableParallel, RunnableLambda

from operator import itemgetter

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from deep_translator import GoogleTranslator

class SearchService:
    def __init__(self, faiss_service, docs: list[Document]):
        """
        초기화 시 VectorService에서 생성된 vectorstore와
        DB에서 가져온 docs를 주입 받습니다.
        """
        self.faiss_service = faiss_service
        self.docs = docs

        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            print("NLTK stopwords downloading...")
            nltk.download('stopwords')
            self.stop_words = set(stopwords.words('english'))

        # 논문 도메인 불용어
        academic_stops = {
            # [형식/지칭]
            'paper', 'article', 'study', 'studies', 'research', 'work',
            
            # [방법론]
            'method', 'methods', 'methodology', 'approach', 'approaches',
            'technique', 'techniques', 'propose', 'proposed', 'present',
            'base', 'based', 'use', 'used', 'using', 'via',
            
            # [결과/분석]
            'result', 'results', 'experimental', 'experiment', 
            'analysis', 'evaluation', 'performance', 'data',
            
            # [수식어]
            'new', 'novel', 'recent', 'advanced',
            
            # [표기/인용]
            'et', 'al', 'fig', 'figure', 'table', 'eq', 'equation', 
            'sec', 'section', 'doi', 'vol', 'pp'
        }

        # 집합 합치기
        self.stop_words.update(academic_stops)

        self.stemmer = PorterStemmer() # 어간 추출
        self.translator = GoogleTranslator(source='auto', target='en') # 번역

        self.hybrid_retriever = self.HybridRetriever()

    def preprocess_func(self, text: str):
        # 1. 소문자 변환
        text = text.lower()
        
        # 2. 특수문자 제거
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        # 3. 토큰화 (공백 기준)
        tokens = text.split()
        
        # 4. 불용어 제거 및 Stemming 적용
        processed_tokens = []
        for t in tokens:
            if t not in self.stop_words:
                # 어간 추출
                stemmed_word = self.stemmer.stem(t)
                processed_tokens.append(stemmed_word)
                
        return processed_tokens
    
    def SparseRetriever(self):
        """
        키워드 기반 검색기(BM25) 반환
        """
        bm25_retriever = BM25Retriever.from_documents(self.docs, preprocess_func=self.preprocess_func)
        bm25_retriever.k = 60
        return bm25_retriever

    def DenseRetriever(self):
        """
        의미 기반 검색기 반환
        """
        def search_faiss(query: str):
            results = self.faiss_service.search_by_text(query, k=60)
            return [
                Document(
                    page_content=f"Title: {res.get("title")}\nAbstract: {res.get("abstract")}",
                    metadata={
                        "arxiv_id": res.get("arxiv_id"),
                        "title": res.get("title"),
                        "pdf_url": res.get("pdf_url"),
                        "abstract": res.get("abstract"),
                        "score": res.get("score")
                    }
                ) for res in results
            ]
        
        return RunnableLambda(search_faiss)

    def HybridRetriever(self):
        """
        하이브리드 검색기 반환
        """
        sparse_retriever = self.SparseRetriever()
        dense_retriever = self.DenseRetriever()

        # [검증 함수] BM25로 들어가는 데이터 확인
        def check_sparse_input(query):
            print(f"\n✅ [검증] BM25(Sparse) 실행 -> 입력값: '{query}' (번역)")
            return query

        # [검증 함수] Dense로 들어가는 데이터 확인
        def check_dense_input(query):
            print(f"✅ [검증] Granite(Dense) 실행 -> 입력값: '{query}' (원본)")
            return query

        # 1. 두 검색기를 병렬로 실행하여 각각 결과를 가져오게 설정
        retrievers_chain = RunnableParallel({
            "sparse": itemgetter("translated_query") | RunnableLambda(check_sparse_input) | sparse_retriever,
            "dense": itemgetter("original_query") | RunnableLambda(check_dense_input) | dense_retriever
        })

        # 2. 두 결과를 합치고 순위를 재조정하는 RRF 함수 정의
        def rrf_merge(results: dict) -> list[Document]:
            sparse_docs = results['sparse']
            dense_docs = results['dense']
            
            doc_scores = {}
            k_constant = 60  # RRF 계산식의 일반적인 상수

            # (1) Sparse 결과
            for rank, doc in enumerate(sparse_docs, 1):
                # arxiv_id를 키로 사용하여 중복 제거
                doc_key = doc.metadata['arxiv_id'] 
                if doc_key not in doc_scores: # -> 새로운 arxiv_id가 나오면
                    doc_scores[doc_key] = {"doc": doc, "score": 0.0, "sparse_rank": None, "dense_rank": None}
                # RRF 계산식: 1 / (k + rank)
                doc_scores[doc_key]["sparse_rank"] = rank
                doc_scores[doc_key]["score"] += (1 / (k_constant + rank))

            # (2) Dense 결과
            for rank, doc in enumerate(dense_docs, 1):
                doc_key = doc.metadata['arxiv_id']
                if doc_key not in doc_scores:
                    doc_scores[doc_key] = {"doc": doc, "score": 0.0, "sparse_rank": None, "dense_rank": None}
                doc_scores[doc_key]["dense_rank"] = rank
                doc_scores[doc_key]["score"] += (1 / (k_constant + rank))

            # (3) 고득점순 정렬
            sorted_results = sorted(
                doc_scores.values(), 
                key=lambda x: x["score"], 
                reverse=True
            )[:20] # Top-20
            
            # (4) 메타데이터에 정보 주입 후 문서 리스트 반환
            recommend_docs = []
            for final_rank, info in enumerate(sorted_results, 1):
                doc = info["doc"]
                
                # 기존 메타데이터 유지하면서 랭크/점수 정보 추가
                doc.metadata.update({
                    "rrf_score": round(info["score"], 4),      # 최종 RRF 점수
                    "sparse_rank": info["sparse_rank"],        # 키워드 검색 등수 (없으면 None)
                    "dense_rank": info["dense_rank"],          # 벡터 검색 등수 (없으면 None)
                    "final_rank": final_rank                   # 최종 등수
                })
                recommend_docs.append(doc)
                
            return recommend_docs

        # 3. 체인 생성: [병렬 검색] -> [RRF 병합]
        hybrid_chain = retrievers_chain | RunnableLambda(rrf_merge)

        return hybrid_chain
    
    def check_language(self, query_input: str) -> str:
        """
        query에 한국어가 포함되어있는지 여부 확인
        """
        ko_re = re.compile('[\uac00-\ud7a3]+')
        if ko_re.search(query_input):
            return 'ko'
        return 'en'

    async def search(self, query: str):
        """
        하이브리드 검색 수행
        """
        lang = self.check_language(query)

        if lang == 'ko':
            translated_query = self.translator.translate(query)
        else:
            translated_query = query

        # 번역된 쿼리로 실행
        return await self.hybrid_retriever.ainvoke({
            "original_query": query,             # -> Dense
            "translated_query": translated_query # -> BM25
        })