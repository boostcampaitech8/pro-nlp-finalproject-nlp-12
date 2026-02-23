import time
from sentence_transformers import SentenceTransformer
from typing import List
from src.database.mysql import get_mysql_db
from sqlalchemy import text
import numpy as np
import pandas as pd
import gc
import torch

def load_model(model_name: str):
    model = SentenceTransformer(model_name, trust_remote_code=True, device="cuda")

    if "e5" in model_name.lower():
        model.prompts = {"query": "query: ", "passage": "passage: "}
    elif "bge" in model_name.lower():
        model.prompts = {"query": "Represent this sentence for searching relevant passages: "}

    return model

def eval_latency(
    model,
    test_data: List[str]
):
    # --- 1. 단일 임베딩 속도 측정 ---
    start_time = time.perf_counter()
    for text in test_data:
        model.encode(text, show_progress_bar=False)
    single_total_time = time.perf_counter() - start_time
    # 문장 1개를 처리할 때 걸리는 시간
    avg_latency = single_total_time / len(test_data)

    # ---2. 배치 임베딩 속도 측정 ---
    start_time = time.perf_counter()
    model.encode(test_data, batch_size=32, show_progress_bar=False)
    batch_total_time = time.perf_counter() - start_time
    # 1초 동안 처리하는 문서의 양
    docs_per_sec = len(test_data) / batch_total_time

    return {
        "avg_latency(ms)": avg_latency * 1000,
        "throughput(docs/sec)": docs_per_sec
    }

def get_test_data(limit=100):
    with get_mysql_db() as db:
        query = text("SELECT title, abstract FROM papers LIMIT :limit")
        result = db.execute(query, {"limit": limit}).fetchall()
        return [f"Title: {row.title} Abstract: {row.abstract}" for row in result]
    
if __name__ == "__main__":
    db_samples = get_test_data()

    model_names = [
        "Qwen/Qwen3-Embedding-0.6B",
        "intfloat/multilingual-e5-large-instruct",
        "google/embeddinggemma-300m",
        "Lajavaness/bilingual-embedding-large",
        "OrdalieTech/Solon-embeddings-large-0.1",
        "jinaai/jina-embeddings-v3",
        "BAAI/bge-m3"
    ]

    results_list = []

    for model_name in model_names:
        if 'model' in locals():
            del model
        gc.collect()
        torch.cuda.empty_cache()

        model = load_model(model_name)

        # Warm-up: 초기 오버헤드 제거
        model.encode(db_samples[:20], show_progress_bar=False)

        latencies = []
        throughputs = []

        for i in range(5):
            print(f"\n[ {model_name} {i + 1}]")
            res = eval_latency(model, db_samples)
        
            l, t = res['avg_latency(ms)'], res['throughput(docs/sec)']
            latencies.append(l)
            throughputs.append(t)

            print(f"    [{i+1}/5] Latency: {l:.2f}ms | Throughput: {t:.2f}docs/s")

        model_res = {
            "model": model_name,
            "latency_avg": np.mean(latencies),
            "latency_std": np.std(latencies),
            "throughput_avg": np.mean(throughputs),
            "throughput_std": np.std(throughputs),
        }
        results_list.append(model_res)

    df = pd.DataFrame(results_list)

    df = df.sort_values(by="latency_avg", ascending=True)

    print("\n" + "="*80)
    print("최종 벤치마크 결과 (Latency 기준 오름차순)")
    print("="*80)
    print(df.to_string(index=False))

    df.to_csv("benchmark_results.csv", index=False, encoding='utf-8-sig')