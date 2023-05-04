from sqlalchemy.orm import Session

from app.models import Config


def set_config(db: Session, key: str, value: str):
    db_obj = db.query(Config).filter(Config.name == key).first()
    if not db_obj:
        db_obj = Config(name=key, value=value)
    else:
        db_obj.value = value
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)


def get_config(db: Session, key: str):
    return db.query(Config).filter(Config.name == key).first()
