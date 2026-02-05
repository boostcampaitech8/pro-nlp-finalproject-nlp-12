from src.database.mysql import get_mysql_db
from src.entity.user_event import UserEvent, EventType

class UserEventRepository:
    @staticmethod
    def save_click(user_id: int, paper_id: int):
        """
        user_id, paper_id를 기반으로 클릭 이벤트를 저장합니다.
        """
        with get_mysql_db() as db:
            # 기존에 저장된 데이터가 있는지 확인
            is_exists = db.query(UserEvent).filter(
                UserEvent.user_id==user_id,
                UserEvent.paper_id==paper_id,
                UserEvent.event_type==EventType.click
            ).first()

            # 존재하지 않을 때만 저장
            if not is_exists:
                click_event = UserEvent(
                    user_id=user_id,
                    paper_id=paper_id,
                    event_type=EventType.click
                )

                db.add(click_event)
                db.commit()