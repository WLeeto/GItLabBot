import sqlalchemy as sq
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "User"

    id = sq.Column(sq.Integer, primary_key=True)
    tg_id = sq.Column(sq.BIGINT, nullable=True)
    tg_name = sq.Column(sq.Text, nullable=False)
    git_name = sq.Column(sq.Text, nullable=False)
    git_id = sq.Column(sq.BIGINT, nullable=False)
    default_project_id = sq.Column(sq.BIGINT, nullable=True)

    def __str__(self):
        return f"{self.id}: {self.tg_id}, {self.tg_name}, {self.git_id}"
