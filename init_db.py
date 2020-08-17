from config.db import SessionLocal, BaseModel, engine
from wallet import _AllocableBaseModel

db = SessionLocal()


def main():
    BaseModel.metadata.create_all(bind=engine)
    _AllocableBaseModel.metadata.create_all(bind=engine)


if __name__ == '__main__':
    main()
