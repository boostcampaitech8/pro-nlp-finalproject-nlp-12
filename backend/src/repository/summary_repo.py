from sqlalchemy.orm import Session
from src.entity.summary import Summary, SummaryType
from typing import List, Dict

class SummaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, paper_id: int, summary_infos: List[Dict[str, str]]):
        """
        논문 요약 결과를 저장합니다.

        params: summary_infos
        [
            {
                "summary_type": ~~,
                "summary_text": ~~,
            },
            {
                "summary_type": ~~,
                "summary_text": ~~,
            },
            ...
        ]
        """
        for summary_info in summary_infos:
            new_summary = Summary(
                summary_type=summary_info.get("summary_type"),
                summary_text=summary_info.get("summary_text"),
                paper_id=paper_id
            )
                
            self.db.add(new_summary)
        self.db.commit()

    def get_summaries_except_keypoint(self, paper_id: int):
        """
        keypoint를 제외한 요약을 반환합니다.
        """
        results = self.db.query(
            Summary.paper_id,
            Summary.summary_type,
            Summary.summary_text
        ).filter(
            Summary.paper_id==paper_id,
            Summary.summary_type!=SummaryType.keypoint  # keypoint 제외
        ).all()

        return results