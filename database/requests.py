import sqlalchemy
from sqlalchemy.orm import sessionmaker

from create_logger import logger
from database.models import Base, User

import os


class database:
    def __init__(self):
        DSN = os.environ.get("GITLABBOT_DB_DSN")

        self.engine = sqlalchemy.create_engine(DSN)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)
        logger.info('Таблицы созданы согласно models.py')

    def drop_tables(self) -> None:
        Base.metadata.drop_all(self.engine)
        logger.info('Все таблицы удалены, все пропало !!!')

    def get_user_by_tg_nickname(self, tg_name: str) -> object or False:
        result = self.session.query(User).filter(User.tg_name.ilike(tg_name)).first()
        return result if result else False

    def get_user_by_id(self, id: int) -> object or False:
        result = self.session.query(User).filter(User.id == id).first()
        return result if result else False

    def all_users(self) -> list:
        result = self.session.query(User).all()
        return result
