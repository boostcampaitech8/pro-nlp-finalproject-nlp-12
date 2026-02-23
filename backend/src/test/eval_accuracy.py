from src.database.mysql import SessionLocal
from src.client.faiss_store import get_faiss_store
from src.repository.paper_repo import PaperRepository
import os, json
import numpy as np
import pandas as pd
from src.entity.base import init_db
from tqdm import tqdm
import src.client.faiss_store as faiss_module

def load_json_data():
    file_path = "src/test/ground_truth_silver.json"

    with open(file_path, "r", encoding="utf-8") as f:
        eval_dataset = json.load(f)

    return eval_dataset

def get_docs():
    db = SessionLocal()
    try:
        paper_repository = PaperRepository(db)
        return paper_repository.get_papers_as_documents()
    finally:
        db.close()

def calculate_ap(relevant_ids, retrieved_ids):
    """
    Average Precision 계산 (MAP의 기초)
    """
    hits = 0
    sum_precisions = 0

    for i, res_id in enumerate(retrieved_ids):
        if res_id in relevant_ids:
            hits += 1
            precision_at_i = hits / (i + 1)
            sum_precisions += precision_at_i

    return sum_precisions / len(relevant_ids) if relevant_ids else 0

def calculate_ndcg(rel_map, retrieved_ids, k=10):
    """
    NDCG 계산 (rel_map: {arxiv_id: score})
    """
    dcg = 0
    for i, res_id in enumerate(retrieved_ids[:k]):
        rel = rel_map.get(res_id, 0)
        dcg += (2 ** rel - 1) / np.log2(i + 2)

    ideal_rels = sorted(rel_map.values(), reverse=True)[:k]
    idcg = sum((2**rel - 1) / np.log2(i + 2) for i, rel in enumerate(ideal_rels))
    
    return dcg / idcg if idcg > 0 else 0

if __name__ == "__main__":
    init_db()
    
    model_dims = {
        "Qwen/Qwen3-Embedding-0.6B": 1536,
        "intfloat/multilingual-e5-large-instruct": 1024,
        "google/embeddinggemma-300m": 1024,
        "Lajavaness/bilingual-embedding-large": 1024,
        "OrdalieTech/Solon-embeddings-large-0.1": 1024,
        "jinaai/jina-embeddings-v3": 1024,
        "BAAI/bge-m3": 1024
    }

    # 인덱스 저장 디렉토리 생성
    os.makedirs("./faiss_indexes", exist_ok=True)

    eval_dataset = load_json_data()
    docs = get_docs()

    doc_map = {p.metadata["paper_id"]: p for p in docs}

    performance_summary = []

    model_pbar = tqdm(model_dims.items(), desc="Overall Progress")
    for model_name, dim in model_dims.items():
        faiss_module._STORE = None

        safe_name = model_name.split('/')[-1]
        model_pbar.set_description(f"Evaluating {safe_name}")

        path = f"./faiss_indexes/index.bin"

        faiss_store = get_faiss_store(dim, path, model_name)
        faiss_store.update_papers(docs)

        ap_scores = []
        ndcg_scores = []

        for item in eval_dataset:
            query = item["query"]

            # 모델별 Prefix 추가 로직
            if "e5" in model_name.lower():
                query = f"query: {query}"
            elif "bge" in model_name.lower():
                query = f"Represent this query for retrieving relevant documents: {query}"
            elif "kalm" in model_name.lower():
                instruction = "Given a query, retrieve documents that answer the query\nQuery: "
                query = f"{instruction}{query}"

            # NDCG용 ground truth
            rel_map = {p["arxiv_id"]: p["rel_score"] for p in item["ground_truth"]}

            # MAP용 ground truth
            relevant_ids = list(rel_map.keys())

            _, ids = faiss_store.search_by_query_str(query, k=10)

            # 검색 수행
            retrieved = []
            for pid in ids:
                if pid != -1 and pid in doc_map:
                    # pid(paper_id)를 key로 사용하여 안전하게 문서 획득
                    retrieved.append(doc_map[pid].metadata["arxiv_id"])

            ap_scores.append(calculate_ap(relevant_ids, retrieved))
            ndcg_scores.append(calculate_ndcg(rel_map, retrieved, k=10))

        mean_ap = np.mean(ap_scores)
        mean_ndcg = np.mean(ndcg_scores)

        print(f" {model_name} -> MAP: {mean_ap:.4f}, NDCG: {mean_ndcg:.4f}")

        performance_summary.append({
            "Model": model_name,
            "MAP@10": round(mean_ap, 4),
            "NDCG@10": round(mean_ndcg, 4)
        })

    df = pd.DataFrame(performance_summary)

    df = df.sort_values(by="NDCG@10", ascending=False)
    
    output_path = "results_openai.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("\n" + "="*50)
    print(f"평가 완료! 결과가 '{output_path}'에 저장되었습니다.")
    print(df)
    print("="*50)