from src.database.mysql import get_mysql_db
from src.entity.summary import Summary, SummaryType
from src.entity.paper import Paper
from typing import List, Dict

class SummaryRepository:
    @staticmethod
    def save(paper_id: int, summary_infos: List[Dict[str, str]]):
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
        with get_mysql_db() as db:
            for summary_info in summary_infos:
                new_summary = Summary(
                    summary_type=summary_info.get("summary_type"),
                    summary_text=summary_info.get("summary_text"),
                    paper_id=paper_id
                )
                
                db.add(new_summary)
            db.commit()

    @staticmethod
    def get_summaries_except_keypoint(paper_id: int):
        """
        keypoint를 제외한 요약을 반환합니다.
        """
        with get_mysql_db() as db:
            results = db.query(
                Summary.paper_id,
                Summary.summary_type,
                Summary.summary_text
            ).filter(
                Summary.paper_id==paper_id,
                Summary.summary_type!=SummaryType.keypoint  # keypoint 제외
            ).all()

            return results