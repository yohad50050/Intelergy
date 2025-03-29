from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

class DatabaseHandler:
    def __init__(self):
        self.engine = create_engine(
            "mysql+mysqlconnector://root:MyNewPass@localhost/Intelergy",
            pool_size=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        # Create a thread-local session factory
        self.Session = scoped_session(sessionmaker(bind=self.engine))
    
    @contextmanager
    def get_session(self):
        session = self.Session()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            self.Session.remove()  # Important for cleaning up thread-local sessions

db = DatabaseHandler() 