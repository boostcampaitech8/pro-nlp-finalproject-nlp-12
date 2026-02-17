# 📚 10seconds Dataset (papers_v5)

본 데이터셋은 **10seconds 웹 서비스 구동에 필요한 데이터를 구성한 브랜치**입니다.  
학술 연구 분석 및 추천 시스템 구축을 위한 **Relational + Graph 기반 연구 데이터셋**입니다.

<p align="center">
  <img src="https://img.shields.io/badge/Papers-12,777-blue" />
  <img src="https://img.shields.io/badge/Domain-NLP%20%7C%20AI-green" />
  <img src="https://img.shields.io/badge/Source-Survey%20%2B%20PyTorch%20KR-orange" />
  <img src="https://img.shields.io/badge/arXiv-cs.CL%20%7C%20cs.LG%20%7C%20cs.AI-red" />
  <img src="https://img.shields.io/badge/Structure-Relational%20%2B%20Citation%20Graph-purple" />
</p>

<p align="center">
<b>Survey References + PyTorch Korea Weekly AI/ML Picks → arXiv Filter → cs.CL / cs.LG / cs.AI Only → Total 12,777 Papers</b>
</p>

---

## 📌 Dataset Collection Criteria

본 논문 데이터셋은 아래 기준에 따라 수집되었습니다.  
총 논문 개수는 **12,777개** 입니다.

### 1) Survey 논문 References 수집

- [ABigSurvey (NiuTrans GitHub)](https://github.com/NiuTrans/ABigSurvey?tab=readme-ov-file#computational-social-science-and-social-media)
- 해당 Survey 논문의 모든 reference를 수집하여 연구 대표성을 확보했습니다.

---

### 2) PyTorch Korea Weekly AI/ML Picks 수집

- [PyTorch Korea Weekly AI/ML Picks](https://discuss.pytorch.kr/t/2026-01-26-02-01-ai-ml/8895) 
- 2025–2026년 매주 추천되는 AI/ML 논문 중 최신 논문을 반영했습니다.
- 이 중 **cs.CL 논문만 선별**하여 최신 NLP 트렌드를 유지했습니다.

---

### 3) arXiv 논문만 유지

- 수집된 논문 중 **arXiv 논문만 포함**하여 형식 통일성을 확보했습니다.

---

### 4) Primary Category 필터링

다음 arXiv Primary Category에 해당하는 논문만 최종 포함:

- `cs.LG`
- `cs.AI`
- `cs.CL`

---

### 🎯 Why These Criteria?

- 최신 AI/ML 트렌드 반영
- Survey 기반 연구 대표성 확보
- 형식 통일성 유지 (arXiv only)
- 현재 팀 규모에서 **지속 관리 가능한 최대 규모(12,777편)** 유지

---

# 📁 Table Description

---

## 1️⃣ papers.csv

논문의 기본 메타데이터 정보

| Column | Type | Description |
|---------|------|-------------|
| id | int (PK, AI) | 내부 논문 ID |
| arxiv_id | varchar(50) | arXiv ID |
| title | varchar(500) | 논문 제목 |
| pdf_url | varchar(1000) | PDF 링크 |
| abstract | text | 초록 |
| citation_count | int | 총 인용 수 |
| influential_citation_count | int | 영향력 있는 인용 수 |
| reference_count | int | 참고문헌 수 |
| published_date | date | 출판일 |
| updated_date | date | 수정일 |
| created_at | timestamp | 생성 시각 |
| updated_at | timestamp | 수정 시각 |

### 특징

- arxiv_id는 Unique Key
- 추천 모델 및 citation graph의 seed 노드 역할 수행

---

## 2️⃣ citation_edges.csv

논문 간 인용 관계를 나타내는 Directed Graph 구조

| Column | Type | Description |
|---------|------|-------------|
| id | int (PK, AI) | 내부 ID |
| seed_id | int (FK → papers.id) | 인용하는 논문 |
| cited_paper_id | int (FK → papers.id) | 인용당한 논문 |
| is_influential | tinyint(1) | 영향력 인용 여부 |

### 구조적 특징

- Self-referencing Graph
- UNIQUE(seed_id, cited_paper_id)
- Directed Edge
- Influence flag 포함

→ Citation Network 분석  
→ GNN 학습 데이터 구성 가능  
→ 영향력 기반 랭킹 모델 실험 가능  

---

## 3️⃣ categories.csv

연구 카테고리 정보

| Column | Type | Description |
|---------|------|-------------|
| id | int (PK, AI) | 카테고리 ID |
| category_type | text | 카테고리 이름 |

### 예시

- Machine Translation  
- Information Retrieval  
- Question Answering  
- Text Summarization  
- Large Language Models  

---

## 4️⃣ papers_categories.csv

논문과 카테고리의 다대다(M:N) 관계 테이블

| Column | Type | Description |
|---------|------|-------------|
| id | int (PK, AI) | 내부 ID |
| paper_id | int (FK → papers.id) | 논문 ID |
| category_id | int (FK → categories.id) | 카테고리 ID |

### 특징

- Multi-label Classification 구조
- UNIQUE(paper_id, category_id)

→ 멀티 라벨 추천 모델 실험 가능  
→ 카테고리 기반 사용자 프로파일링 가능  

---

## 5️⃣ summaries.csv

논문별 다중 요약 정보를 저장하는 테이블

| Column | Type | Description |
|---------|------|-------------|
| id | int (PK, AI) | 내부 ID |
| paper_id | int (FK → papers.id) | 논문 ID |
| summary_text | text | 요약 내용 |
| summary_type | varchar(50) | 요약 타입 |
| created_at | timestamp | 생성 시각 |

### 🔎 Summary Type

- motivation  
- methodology  
- performance  
- significance  
- keypoint  

### 특징

- 하나의 논문은 여러 summary_type을 가질 수 있음 (1:N 구조)
- Multi-view Summary Layer 구조
- Huggingface Datasets에서 확인 가능 (데이터셋 크기 초과 문제로 인해, 깃허브에 업로드하지 못함.)
[hugging face Datasets](https://huggingface.co/datasets/gahyunlee/paper_summaries)
---

# 🏗 Relational Structure

```
papers
│
├── citation_edges (self-referencing directed graph)
│
├── papers_categories ── categories
│
└── summaries
```

### 관계 구조

- Citation → Self Graph
- Category → M:N
- Summary → 1:N
- 전체 구조 → Research Knowledge Graph + Multi-summary Layer

---

# 📊 Data Characteristics

- Domain: Natural Language Processing (NLP)
- Structure: Relational + Directed Graph Hybrid
- Citation: Directed Graph
- Category: Multi-label
- Summary: Multi-type, Multi-instance

### Designed For

- Research Trend Analysis
- Knowledge Graph Construction
- Graph Neural Network Experiments
- LLM-based Multi-summary Modeling
- Academic Recommendation Systems
- Personalized Feed Ranking
- RAG Pipeline Research

---

# ⚙️ Suggested Tech Stack

- Python
- Pandas
- NetworkX
- PyTorch Geometric
- Neo4j
- MySQL
- FastAPI
- AWS
- Naver Hyper Clova X

---

# 🚀 10seconds Web Usage

본 데이터는 10seconds 웹 서비스에서 다음 기능을 지원합니다:

- 논문 추천 피드 구성
- 카테고리 기반 사용자 관심사 매칭
- Multi-summary 기반 빠른 논문 이해

---

# 👩‍💻 Maintainer

10seconds Research Team
