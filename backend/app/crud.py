import uuid
from typing import Any

from sqlmodel import Session, func, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Competition,
    Contest,
    DataSync,
    Item,
    ItemCreate,
    Judoka,
    Rating,
    RatingFormula,
    RatingFormulaCreate,
    RatingFormulaUpdate,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# RatingFormula CRUD

def get_rating_formulas(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> list[RatingFormula]:
    """Список формул рейтинга с пагинацией и опциональным фильтром по is_active."""
    statement = select(RatingFormula).offset(skip).limit(limit).order_by(RatingFormula.name)
    if is_active is not None:
        statement = statement.where(RatingFormula.is_active == is_active)
    return list(session.exec(statement).all())


def get_rating_formula_by_id(
    *, session: Session, formula_id: uuid.UUID
) -> RatingFormula | None:
    """Формула рейтинга по id."""
    return session.get(RatingFormula, formula_id)


def create_rating_formula(
    *, session: Session, formula_in: RatingFormulaCreate
) -> RatingFormula:
    """Создать формулу рейтинга."""
    db_formula = RatingFormula.model_validate(formula_in)
    session.add(db_formula)
    session.commit()
    session.refresh(db_formula)
    return db_formula


def update_rating_formula(
    *,
    session: Session,
    db_formula: RatingFormula,
    formula_in: RatingFormulaUpdate,
) -> RatingFormula:
    """Обновить формулу рейтинга."""
    update_data = formula_in.model_dump(exclude_unset=True)
    db_formula.sqlmodel_update(update_data)
    session.add(db_formula)
    session.commit()
    session.refresh(db_formula)
    return db_formula


def delete_rating_formula(*, session: Session, formula_id: uuid.UUID) -> None:
    """Удалить формулу рейтинга."""
    formula = session.get(RatingFormula, formula_id)
    if formula:
        session.delete(formula)
        session.commit()


# Competition CRUD

def get_competitions(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    id_country: int | None = None,
) -> tuple[list[Competition], int]:
    """Список соревнований с пагинацией. Возвращает (data, count)."""
    statement = select(Competition).order_by(Competition.id.desc())
    count_statement = select(func.count()).select_from(Competition)
    if id_country is not None:
        statement = statement.where(Competition.id_country == id_country)
        count_statement = count_statement.where(Competition.id_country == id_country)
    count = session.exec(count_statement).one()
    rows = session.exec(statement.offset(skip).limit(limit)).all()
    return (list(rows), count)


def get_competition_by_id(
    *, session: Session, competition_id: int
) -> Competition | None:
    """Соревнование по id."""
    return session.get(Competition, competition_id)


# Contest CRUD

def get_contests(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    competition_id: int | None = None,
    judoka_id: int | None = None,
) -> list[Contest]:
    """Список поединков с фильтрами по соревнованию и/или дзюдоисту."""
    statement = select(Contest).order_by(Contest.id.desc())
    if competition_id is not None:
        statement = statement.where(Contest.id_competition == competition_id)
    if judoka_id is not None:
        statement = statement.where(
            (Contest.id_judoka_blue == judoka_id) | (Contest.id_judoka_white == judoka_id)
        )
    return list(session.exec(statement.offset(skip).limit(limit)).all())


def get_contest_by_id(*, session: Session, contest_id: int) -> Contest | None:
    """Поединок по id."""
    return session.get(Contest, contest_id)


# Judoka CRUD

def get_judokas(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    id_country: int | None = None,
) -> tuple[list[Judoka], int]:
    """Список дзюдоистов с пагинацией. Возвращает (data, count)."""
    statement = select(Judoka).order_by(Judoka.family_name, Judoka.given_name)
    count_statement = select(func.count()).select_from(Judoka)
    if id_country is not None:
        statement = statement.where(Judoka.id_country == id_country)
        count_statement = count_statement.where(Judoka.id_country == id_country)
    count = session.exec(count_statement).one()
    rows = session.exec(statement.offset(skip).limit(limit)).all()
    return (list(rows), count)


def get_judoka_by_id(*, session: Session, judoka_id: int) -> Judoka | None:
    """Дзюдоист по id."""
    return session.get(Judoka, judoka_id)


def get_judoka_contests(
    *,
    session: Session,
    judoka_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Contest]:
    """Поединки дзюдоиста."""
    statement = (
        select(Contest)
        .where(
            (Contest.id_judoka_blue == judoka_id) | (Contest.id_judoka_white == judoka_id)
        )
        .order_by(Contest.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_judoka_ratings(*, session: Session, judoka_id: int) -> list[Rating]:
    """Рейтинги дзюдоиста."""
    statement = select(Rating).where(Rating.id_judoka == judoka_id)
    return list(session.exec(statement).all())


# Rating CRUD

def get_ratings(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    formula_id: uuid.UUID | None = None,
    judoka_id: int | None = None,
) -> list[Rating]:
    """Список рейтингов с фильтрами."""
    statement = select(Rating).order_by(Rating.id.desc())
    if formula_id is not None:
        statement = statement.where(Rating.formula_id == formula_id)
    if judoka_id is not None:
        statement = statement.where(Rating.id_judoka == judoka_id)
    return list(session.exec(statement.offset(skip).limit(limit)).all())


def get_leaderboard(
    *,
    session: Session,
    formula_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Rating]:
    """Таблица лидеров по формуле (топ по рейтингу)."""
    statement = (
        select(Rating)
        .where(Rating.formula_id == formula_id)
        .order_by(Rating.id.desc())  # при необходимости заменить на поле «рейтинг»
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_rating_by_judoka_and_formula(
    *,
    session: Session,
    judoka_id: int,
    formula_id: uuid.UUID,
) -> Rating | None:
    """Рейтинг дзюдоиста по одной формуле."""
    statement = select(Rating).where(
        Rating.id_judoka == judoka_id,
        Rating.formula_id == formula_id,
    )
    return session.exec(statement).first()


def get_rating_history(
    *,
    session: Session,
    rating_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Any]:
    """История изменений рейтинга. Пока нет модели истории — возвращаем пустой список."""
    return []


# DataSync CRUD

def get_data_syncs(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
) -> tuple[list[DataSync], int]:
    """Список логов синхронизации. Возвращает (data, count)."""
    statement = select(DataSync).order_by(DataSync.started_at.desc())
    count_statement = select(func.count()).select_from(DataSync)
    if status is not None:
        statement = statement.where(DataSync.status == status)
        count_statement = count_statement.where(DataSync.status == status)
    count = session.exec(count_statement).one()
    rows = session.exec(statement.offset(skip).limit(limit)).all()
    return (list(rows), count)


def get_data_sync_by_id(
    *, session: Session, sync_id: uuid.UUID
) -> DataSync | None:
    """Запись лога синхронизации по id."""
    return session.get(DataSync, sync_id)
