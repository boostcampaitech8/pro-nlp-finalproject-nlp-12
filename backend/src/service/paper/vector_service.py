import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

class VectorService:
    def __init__(self, model_name: str = "ibm-granite/granite-embedding-107m-multilingual"):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},  # GPU가 있으면 'cuda'
            encode_kwargs={"normalize_embeddings": True}, # 정규화
        )
        self.index_path = "data/faiss_index"
        self.vectorstore = None

    def initialize_index(self, all_papers: list[Document]):
        """
        인덱스를 로드하거나, 없으면 새로 생성하고, 추가된 데이터가 있으면 업데이트합니다.
        """
        if os.path.exists(self.index_path):
            self.vectorstore = FAISS.load_local(
                self.index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )

            # 신규 데이터 확인(metadata의 arxiv_id 기준)
            indexed_ids = set([
                doc.metadata["arxiv_id"]
                for doc in self.vectorstore.docstore._dict.values()
            ])
            new_docs = [
                doc for doc in all_papers
                if doc.metadata["arxiv_id"] not in indexed_ids
            ]

            if new_docs:
                # 신규 데이터는 추가 인덱싱
                self.vectorstore.add_documents(new_docs)
                self.vectorstore.save_local(self.index_path)
        else:
            # 인덱스가 없으면 처음부터 생성
            self.vectorstore = FAISS.from_documents(all_papers, self.embeddings)
            self.vectorstore.save_local(self.index_path)

        return self.vectorstore
        
