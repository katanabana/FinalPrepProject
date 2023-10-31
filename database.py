from sqlalchemy import text, create_engine, select, join, orm
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, Session


class Descriptor:
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner):
        return self.function()


class ReusableSession(Session):

    def commit(self) -> None:
        super().commit()
        DB.current_session = DB.new_session

    def rollback(self) -> None:
        super().rollback()
        DB.current_session = DB.new_session


class DB:
    server = '(localdb)\\server'  # имя mssql сервера
    db = 'Test'  # имя базы данных
    driver = 'ODBC+Driver+17+for+SQL+Server'
    url = f'mssql://@{server}/{db}?trusted_connection=yes&driver={driver}'
    engine = create_engine(url)
    base = automap_base()
    base.prepare(engine)
    get_session = sessionmaker(engine)
    new_session = Descriptor(get_session)
    current_session = ReusableSession(engine)
