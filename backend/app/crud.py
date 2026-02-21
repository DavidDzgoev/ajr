import uuid
from typing import Any

from sqlmodel import Session, func, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Competition,
    Contest,
    Country,
    DataSync,
    Judoka,
    Rating,
    RatingChange,
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


# RatingFormula CRUD


def get_rating_formulas(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> list[RatingFormula]:
    """Список формул рейтинга с пагинацией и опциональным фильтром по is_active."""
    statement = (
        select(RatingFormula).offset(skip).limit(limit).order_by(RatingFormula.name)
    )
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


def get_countries(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Country], int]:
    """Список стран с пагинацией. Возвращает (data, count)."""
    statement = select(Country).order_by(Country.name)
    count_statement = select(func.count()).select_from(Country)
    count = session.exec(count_statement).one()
    rows = session.exec(statement.offset(skip).limit(limit)).all()
    return (list(rows), count)


def get_country_by_id(*, session: Session, country_id: int) -> Country | None:
    """Страна по id."""
    return session.get(Country, country_id)


# Contest CRUD


def get_contests(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    competition_id: int | None = None,
    judoka_id: int | None = None,
) -> tuple[list[Contest], int]:
    """Список поединков с фильтрами по соревнованию и/или дзюдоисту."""
    statement = select(Contest).order_by(Contest.id.desc())
    count_statement = select(func.count()).select_from(Contest)
    if competition_id is not None:
        statement = statement.where(Contest.id_competition == competition_id)
        count_statement = count_statement.where(
            Contest.id_competition == competition_id
        )
    if judoka_id is not None:
        statement = statement.where(
            (Contest.id_judoka_blue == judoka_id)
            | (Contest.id_judoka_white == judoka_id)
        )
        count_statement = count_statement.where(
            (Contest.id_judoka_blue == judoka_id)
            | (Contest.id_judoka_white == judoka_id)
        )
    count = session.exec(count_statement).one()
    rows = session.exec(statement.offset(skip).limit(limit)).all()
    return (list(rows), count)


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
            (Contest.id_judoka_blue == judoka_id)
            | (Contest.id_judoka_white == judoka_id)
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
    surname: str | None = None,
    weight: str | None = None,
    rating_min: float | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Список рейтингов с фильтрами."""
    statement = (
        select(Rating, Judoka.family_name, Judoka.given_name)
        .select_from(Rating)
        .join(Judoka, Rating.id_judoka == Judoka.id, isouter=True)
        .order_by(Rating.rating_value.desc().nullslast(), Rating.id.desc())
    )
    count_statement = (
        select(func.count())
        .select_from(Rating)
        .join(Judoka, Rating.id_judoka == Judoka.id, isouter=True)
    )
    if formula_id is not None:
        statement = statement.where(Rating.formula_id == formula_id)
        count_statement = count_statement.where(Rating.formula_id == formula_id)
    if judoka_id is not None:
        statement = statement.where(Rating.id_judoka == judoka_id)
        count_statement = count_statement.where(Rating.id_judoka == judoka_id)
    if surname:
        surname_like = f"%{surname.strip()}%"
        statement = statement.where(Judoka.family_name.ilike(surname_like))
        count_statement = count_statement.where(Judoka.family_name.ilike(surname_like))
    if weight:
        weight_like = f"%{weight.strip()}%"
        statement = statement.where(Rating.weight.ilike(weight_like))
        count_statement = count_statement.where(Rating.weight.ilike(weight_like))
    if rating_min is not None:
        statement = statement.where(Rating.rating_value >= rating_min)
        count_statement = count_statement.where(Rating.rating_value >= rating_min)

    count = session.exec(count_statement).one()
    rows = session.exec(statement.offset(skip).limit(limit)).all()

    data: list[dict[str, Any]] = []
    for rating, family_name, given_name in rows:
        row = rating.model_dump()
        row["judoka_family_name"] = family_name
        row["judoka_given_name"] = given_name
        data.append(row)

    return data, count


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
        .order_by(Rating.rating_value.desc().nullslast(), Rating.id.desc())
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


def get_rating_changes(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    judoka_id: int | None = None,
    contest_id: int | None = None,
) -> tuple[list[RatingChange], int]:
    """Изменения рейтинга с фильтрами. Возвращает (data, count)."""
    statement = select(RatingChange).order_by(RatingChange.id.desc())
    count_statement = select(func.count()).select_from(RatingChange)
    if judoka_id is not None:
        statement = statement.where(RatingChange.id_judoka == judoka_id)
        count_statement = count_statement.where(RatingChange.id_judoka == judoka_id)
    if contest_id is not None:
        statement = statement.where(RatingChange.id_contest == contest_id)
        count_statement = count_statement.where(RatingChange.id_contest == contest_id)
    count = session.exec(count_statement).one()
    rows = session.exec(statement.offset(skip).limit(limit)).all()
    return (list(rows), count)


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


def get_data_sync_by_id(*, session: Session, sync_id: uuid.UUID) -> DataSync | None:
    """Запись лога синхронизации по id."""
    return session.get(DataSync, sync_id)
