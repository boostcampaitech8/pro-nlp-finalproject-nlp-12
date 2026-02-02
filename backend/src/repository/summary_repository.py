from src.database.mysql import get_mysql_db
from src.entity.summary import Summary
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
            summaries = [
                Summary(
                    summary_type=summary_info.get("summary_type"),
                    summary_text=summary_info.get("summary_text"),
                    paper_id=paper_id
                )
                for summary_info in summary_infos
            ]

            db.add_all(summaries)
            db.commit()