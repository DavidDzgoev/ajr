import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlalchemy import Column, Text
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# DataSync (Лог синхронизации данных)
class DataSyncBase(SQLModel):
    sync_type: str = Field(
        max_length=50
    )  # "competitions", "contests", "judokas", "full"
    status: str = Field(max_length=50)  # "pending", "running", "completed", "failed"
    started_at: datetime
    completed_at: datetime | None = Field(default=None)
    records_processed: int = Field(default=0)
    records_created: int = Field(default=0)
    records_updated: int = Field(default=0)
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )


class DataSync(DataSyncBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class DataSyncCreate(SQLModel):
    sync_type: str = Field(max_length=50)
    created_by: uuid.UUID | None = None


class DataSyncPublic(DataSyncBase):
    id: uuid.UUID


class DataSyncsPublic(SQLModel):
    data: list[DataSyncPublic]
    count: int


# Country model
class CountryBase(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    ioc: str | None = Field(default=None, max_length=10)
    file_flag: str | None = Field(default=None, max_length=255)


class Country(CountryBase, table=True):
    id: int = Field(primary_key=True)
    judokas: list["Judoka"] = Relationship(back_populates="country_rel")
    competitions: list["Competition"] = Relationship(back_populates="country_rel")


class CountryPublic(CountryBase):
    id: int


class CountriesPublic(SQLModel):
    data: list[CountryPublic]
    count: int


# Judoka model
class JudokaBase(SQLModel):
    family_name: str | None = Field(default=None, max_length=255)
    given_name: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=50)
    judoka_picture: str | None = Field(default=None, max_length=255)
    dob_year: int | None = Field(default=None)
    id_country: int | None = Field(default=None, foreign_key="country.id")


class Judoka(JudokaBase, table=True):
    id: int = Field(primary_key=True)
    country_rel: Country | None = Relationship(back_populates="judokas")
    contests_as_blue: list["Contest"] = Relationship(
        back_populates="judoka_blue",
        sa_relationship_kwargs={"foreign_keys": "[Contest.id_judoka_blue]"},
    )
    contests_as_white: list["Contest"] = Relationship(
        back_populates="judoka_white",
        sa_relationship_kwargs={"foreign_keys": "[Contest.id_judoka_white]"},
    )
    contests_as_winner: list["Contest"] = Relationship(
        back_populates="judoka_winner",
        sa_relationship_kwargs={"foreign_keys": "[Contest.id_winner]"},
    )
    ratings: list["Rating"] = Relationship(back_populates="judoka_rel")
    rating_changes: list["RatingChange"] = Relationship(
        back_populates="judoka_rel",
        sa_relationship_kwargs={"foreign_keys": "[RatingChange.id_judoka]"},
    )


class JudokaPublic(JudokaBase):
    id: int


class JudokasPublic(SQLModel):
    data: list[JudokaPublic]
    count: int


# Competition model
class CompetitionBase(SQLModel):
    date_from: str | None = Field(default=None, max_length=50)
    date_to: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)
    rank_name: str | None = Field(default=None, max_length=100)
    competition_code: str | None = Field(default=None, max_length=100)
    id_country: int | None = Field(default=None, foreign_key="country.id")
    city: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=50)


class Competition(CompetitionBase, table=True):
    id: int = Field(primary_key=True)
    country_rel: Country | None = Relationship(back_populates="competitions")
    contests: list["Contest"] = Relationship(back_populates="competition_rel")


class CompetitionPublic(CompetitionBase):
    id: int


class CompetitionsPublic(SQLModel):
    data: list[CompetitionPublic]
    count: int


# Contest model
class ContestBase(SQLModel):
    id_competition: int | None = Field(default=None, foreign_key="competition.id")
    id_judoka_blue: int | None = Field(default=None, foreign_key="judoka.id")
    id_judoka_white: int | None = Field(default=None, foreign_key="judoka.id")
    id_winner: int | None = Field(default=None, foreign_key="judoka.id")
    is_finished: int | None = Field(default=None)
    duration: str | None = Field(default=None, max_length=50)
    ippon_w: int | None = Field(default=None)
    waza_w: int | None = Field(default=None)
    yuko_w: int | None = Field(default=None)
    penalty_w: int | None = Field(default=None)
    hsk_w: int | None = Field(default=None)
    ippon_b: int | None = Field(default=None)
    waza_b: int | None = Field(default=None)
    yuko_b: int | None = Field(default=None)
    penalty_b: int | None = Field(default=None)
    hsk_b: int | None = Field(default=None)
    round: int | None = Field(default=None)
    round_code: str | None = Field(default=None, max_length=50)
    round_name: str | None = Field(default=None, max_length=255)
    type: int | None = Field(default=None)
    gs: int | None = Field(default=None)
    bye: int | None = Field(default=None)
    fight_no: int | None = Field(default=None)
    weight: str | None = Field(default=None, max_length=50)
    id_weight: int | None = Field(default=None)
    fight_duration: int | None = Field(default=None)
    rank_name: str | None = Field(default=None, max_length=255)
    rating_change_w: int | None = Field(default=None)
    rating_change_b: int | None = Field(default=None)


class Contest(ContestBase, table=True):
    id: int = Field(primary_key=True)
    competition_rel: Competition | None = Relationship(back_populates="contests")
    judoka_blue: Judoka | None = Relationship(
        back_populates="contests_as_blue",
        sa_relationship_kwargs={"foreign_keys": "[Contest.id_judoka_blue]"},
    )
    judoka_white: Judoka | None = Relationship(
        back_populates="contests_as_white",
        sa_relationship_kwargs={"foreign_keys": "[Contest.id_judoka_white]"},
    )
    judoka_winner: Judoka | None = Relationship(
        back_populates="contests_as_winner",
        sa_relationship_kwargs={"foreign_keys": "[Contest.id_winner]"},
    )
    rating_changes: list["RatingChange"] = Relationship(back_populates="contest_rel")


class ContestPublic(ContestBase):
    id: int


class ContestsPublic(SQLModel):
    data: list[ContestPublic]
    count: int


# RatingFormula model (формула рейтинга: название, описание)
class RatingFormulaBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)  # название
    description: str | None = Field(default=None, max_length=2000)  # описание
    is_active: bool = True


class RatingFormula(RatingFormulaBase, table=True):
    __tablename__ = "rating_formula"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ratings: list["Rating"] = Relationship(back_populates="formula_rel")


class RatingFormulaCreate(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool = True


class RatingFormulaPublic(RatingFormulaBase):
    id: uuid.UUID


class RatingFormulaUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None


class RatingFormulasPublic(SQLModel):
    data: list[RatingFormulaPublic]
    count: int


# Rating model
class RatingBase(SQLModel):
    id_judoka: int | None = Field(default=None, foreign_key="judoka.id")
    id_weight: int | None = Field(default=None)
    weight: str | None = Field(default=None, max_length=50)
    formula_id: uuid.UUID | None = Field(default=None, foreign_key="rating_formula.id")
    rating_value: float | None = Field(default=None)


class Rating(RatingBase, table=True):
    id: int = Field(primary_key=True)
    judoka_rel: Judoka | None = Relationship(back_populates="ratings")
    formula_rel: RatingFormula | None = Relationship(back_populates="ratings")


class RatingPublic(RatingBase):
    id: int
    judoka_family_name: str | None = None
    judoka_given_name: str | None = None


class RatingsPublic(SQLModel):
    data: list[RatingPublic]
    count: int


class RatingChangeBase(SQLModel):
    id_judoka: int | None = Field(default=None, foreign_key="judoka.id")
    id_contest: int | None = Field(default=None, foreign_key="contest.id")
    id_opponent: int | None = Field(default=None, foreign_key="judoka.id")
    opponent_rating_at_match: float | None = Field(default=None)
    rating_change: float | None = Field(default=None)
    opponent_rating_change: float | None = Field(default=None)


class RatingChange(RatingChangeBase, table=True):
    __tablename__ = "rating_change"
    id: int = Field(primary_key=True)
    judoka_rel: Judoka | None = Relationship(
        back_populates="rating_changes",
        sa_relationship_kwargs={"foreign_keys": "[RatingChange.id_judoka]"},
    )
    contest_rel: Contest | None = Relationship(back_populates="rating_changes")


class RatingChangePublic(RatingChangeBase):
    id: int


class RatingChangesPublic(SQLModel):
    data: list[RatingChangePublic]
    count: int
