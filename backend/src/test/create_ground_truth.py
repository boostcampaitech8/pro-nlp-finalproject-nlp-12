import json
import os
from tqdm import tqdm
from src.database.mysql import SessionLocal
from src.repository.paper_repo import PaperRepository
from src.client.faiss_store import get_faiss_store
from src.entity.base import init_db
import src.client.faiss_store as faiss_module

def get_docs():
    db = SessionLocal()
    try:
        paper_repository = PaperRepository(db)
        # 상위 500개 혹은 전체 논문을 대상으로 설정 가능
        return paper_repository.get_papers_as_documents(is_limited=True, limit=500)
    finally:
        db.close()

def build_silver_dataset():
    init_db()
    
    # 1. 환경 설정
    input_path = "src/test/ground_truth.json"
    output_path = "src/test/ground_truth_silver.json"
    
    # Teacher 모델 설정
    model_name = "text-embedding-3-large"
    dim = 3072
    index_path = f"./faiss_indexes/openai_teacher.index"

    # 2. 데이터 및 Teacher 모델 로드
    with open(input_path, "r", encoding="utf-8") as f:
        eval_dataset = json.load(f)

    faiss_module._STORE = None
    
    docs = get_docs()
    teacher_store = get_faiss_store(dim, index_path, model_name)
    
    # 인덱스가 비어있다면 빌드
    if teacher_store.total_count == 0:
        teacher_store.update_papers(docs)

    doc_map = {p.metadata["paper_id"]: p for p in docs}

    # 3. Silver GT 생성 로직
    new_dataset = []

    for item in tqdm(eval_dataset, desc="Generating GT"):
        query = item["query"]
        _, ids = teacher_store.search_by_query_str(query, k=10)

        ground_truth_candidates = []
        for i, pid in enumerate(ids):
            # pid가 -1(결과 없음)이 아니고, doc_map에 존재하는 경우만 처리
            if pid != -1 and pid in doc_map:
                target_doc = doc_map[pid]
                meta = target_doc.metadata

                if i < 3:      # 1~3위
                    score = 3
                elif i < 7:    # 4~7위
                    score = 2
                else:          # 8~10위
                    score = 1

                ground_truth_candidates.append({
                    "arxiv_id": meta["arxiv_id"],
                    "title": meta.get("title", ""),
                    "rel_score": score
                })

        new_dataset.append({
            "no": item["no"],
            "query": query,
            "ground_truth": ground_truth_candidates
        })

    # 4. 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_dataset, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    build_silver_dataset()