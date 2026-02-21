"""Service for synchronizing data from judobase."""

import asyncio
import logging
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text
from sqlmodel import Session, select

from app.models import (
    Competition,
    Contest,
    Country,
    DataSync,
    Judoka,
    Rating,
    RatingChange,
    RatingFormula,
)
from app.services.judobase_service import JudobaseService
from app.services.rating_calculator import RatingCalculator, get_calculator

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing data from judobase to database."""

    def __init__(self, session: Session) -> None:
        self.session = session

    async def sync_all(self, created_by: UUID | None = None) -> DataSync:
        """Synchronize all data from judobase and calculate ratings."""
        data_sync = self._create_data_sync_record(created_by)

        try:
            self._clear_synced_data()
            async with JudobaseService() as judobase:
                await self._download_countries(judobase, data_sync)
                await self._download_competitions(judobase, data_sync)
                await self._download_contests_and_judokas(judobase, data_sync)
                await self.download_fomulas(data_sync)
                await self._calculate_ratings()

            self._complete_data_sync_record(data_sync, True)
            logger.info(
                f"Sync completed: {data_sync.records_processed} processed, "
                f"{data_sync.records_created} created, {data_sync.records_updated} updated"
            )

        except Exception as e:
            logger.error(f"Sync failed: {str(e)}", exc_info=True)
            self.session.rollback()
            self._complete_data_sync_record(data_sync, False, str(e))

        return data_sync

    def _clear_synced_data(self) -> None:
        """Remove previously synced data before a full refresh."""
        logger.info("Clearing previously synced data before full sync")
        logger.info("Truncating synced tables")
        self.session.exec(
            text(
                "TRUNCATE TABLE rating_change, rating, contest, competition, judoka, country "
                "RESTART IDENTITY CASCADE"
            )
        )
        self.session.commit()

    async def _download_contests_and_judokas(
        self, judobase: JudobaseService, data_sync: DataSync
    ) -> None:
        """Download contests and judokas from judobase and store in database.

        Judokas are fetched and saved first. Only contests whose blue and white
        judokas were successfully saved are inserted, to avoid FK violations.
        """
        logger.info("Downloading contests and judokas")
        contests = await judobase.get_all_contests()

        judokas_ids = {
            x
            for c in contests
            for x in (c.id_person_blue, c.id_person_white)
            if x is not None
        }
        judokas_ids_list = sorted(judokas_ids)

        tasks = [judobase.get_judoka_by_id(str(jid)) for jid in judokas_ids_list]
        tasks_results = await asyncio.gather(*tasks, return_exceptions=True)

        judokas: list = []
        for i, res in enumerate(tasks_results):
            if isinstance(res, BaseException):
                jid = judokas_ids_list[i] if i < len(judokas_ids_list) else "?"
                logger.warning("Judoka %s fetch failed: %s", jid, res)
                continue
            if res[0] is not None:
                judokas.append(res)

        saved_judoka_ids: set[int] = set()
        for judoka_record in judokas:
            judoka, judoka_id = judoka_record
            judoka_record = Judoka(
                id=judoka_id,
                family_name=judoka.family_name,
                given_name=judoka.given_name,
                gender=judoka.gender,
                judoka_picture=judoka.personal_picture,
                dob_year=judoka.dob_year,
                id_country=judoka.id_country,
            )
            self.session.add(judoka_record)
            saved_judoka_ids.add(judoka_id)
            data_sync.records_created += 1

        skipped_contests = 0
        for contest in contests:
            blue_ok = (
                contest.id_person_blue is None
                or contest.id_person_blue in saved_judoka_ids
            )
            white_ok = (
                contest.id_person_white is None
                or contest.id_person_white in saved_judoka_ids
            )
            if not blue_ok or not white_ok or contest.id_winner == "0":
                skipped_contests += 1
                continue
            contest_record = Contest(
                id_competition=contest.id_competition,
                id_judoka_blue=contest.id_person_blue,
                id_judoka_white=contest.id_person_white,
                id_winner=contest.id_winner,
                is_finished=contest.is_finished,
                duration=contest.duration,
                ippon_w=contest.ippon_w,
                waza_w=contest.waza_w,
                yuko_w=contest.yuko_w,
                penalty_w=contest.penalty_w,
                hsk_w=contest.hsk_w,
                ippon_b=contest.ippon_b,
                waza_b=contest.waza_b,
                yuko_b=contest.yuko_b,
                penalty_b=contest.penalty_b,
                hsk_b=contest.hsk_b,
                round=contest.round,
                round_code=contest.round_code,
                round_name=contest.round_name,
                type=contest.type,
                gs=contest.gs,
                bye=contest.bye,
                fight_no=contest.fight_no,
                weight=contest.weight,
                id_weight=contest.id_weight,
                fight_duration=contest.fight_duration,
                rank_name=contest.rank_name,
            )
            self.session.add(contest_record)
            data_sync.records_created += 1

        if skipped_contests:
            logger.info("Skipped %d contests (missing judoka)", skipped_contests)

    async def _download_countries(
        self, judobase: JudobaseService, data_sync: DataSync
    ) -> None:
        """Download countries from judobase and store in database."""
        logger.info("Downloading countries")
        countries = await judobase.get_all_countries()

        for country in countries:
            country_record = Country(
                id=country.id_country,
                name=country.name,
                ioc=country.ioc,
            )
            self.session.add(country_record)
            data_sync.records_created += 1

    async def _download_competitions(
        self, judobase: JudobaseService, data_sync: DataSync
    ) -> None:
        """Download competitions from judobase and store in database."""
        logger.info("Downloading competitions")
        competitions = await judobase.get_all_competitions()

        for competition in competitions:
            competition_record = Competition(
                id=competition.id_competition,
                date_from=competition.date_from,
                date_to=competition.date_to,
                name=competition.name,
                rank_name=competition.rank_name,
                competition_code=competition.competition_code,
                id_country=competition.id_country,
                city=competition.city,
                timezone=competition.timezone,
            )
            self.session.add(competition_record)
            data_sync.records_created += 1

    async def download_fomulas(self, data_sync: DataSync) -> None:
        """Ensure built-in rating formulas exist in the database."""
        logger.info("Ensuring built-in rating formulas")

        defaults = (
            (
                "elo",
                (
                    "Classic Elo rating system with expected-score updates. "
                    "Good baseline formula for one-on-one matchups."
                ),
            ),
            (
                "glicko",
                (
                    "Glicko-2 rating system that tracks rating deviation and "
                    "volatility to model confidence and performance swings."
                ),
            ),
        )

        existing = {
            formula.name.strip().lower(): formula
            for formula in self.session.exec(select(RatingFormula)).all()
        }

        for name, description in defaults:
            db_formula = existing.get(name)
            if db_formula is None:
                self.session.add(
                    RatingFormula(
                        name=name,
                        description=description,
                        is_active=True,
                    )
                )
                data_sync.records_created += 1
                continue

            updated = False
            if db_formula.description != description:
                db_formula.description = description
                updated = True
            if not db_formula.is_active:
                db_formula.is_active = True
                updated = True

            if updated:
                self.session.add(db_formula)
                data_sync.records_updated += 1

    @staticmethod
    def _resolve_formula_type(name: str) -> str | None:
        """Map formula DB name to calculator type."""
        normalized = name.strip().lower()
        if normalized == "elo":
            return "elo"
        if normalized == "glicko":
            return "glicko"
        return None

    async def _calculate_ratings(self) -> None:
        """Calculate ratings for all active formulas from the database."""
        logger.info("Calculating ratings")

        formulas = list(
            self.session.exec(
                select(RatingFormula)
                .where(RatingFormula.is_active.is_(True))
                .order_by(RatingFormula.name.asc())
            ).all()
        )
        if not formulas:
            logger.warning("No active rating formulas found, skipping rating calculation")
            return

        stmt = (
            select(Contest)
            .join(Competition, Contest.id_competition == Competition.id)
            .order_by(
                Competition.date_from.asc().nullslast(),
                Contest.fight_no.asc().nullslast(),
                Contest.id.asc(),
            )
        )
        contests = list(self.session.exec(stmt).all())

        calculators: list[tuple[RatingFormula, str, RatingCalculator]] = []
        for formula in formulas:
            formula_type = self._resolve_formula_type(formula.name)
            if formula_type is None:
                logger.warning(
                    "Skipping unsupported formula '%s' (id=%s)",
                    formula.name,
                    formula.id,
                )
                continue
            calculators.append((formula, formula_type, get_calculator(formula_type, {})))

        if not calculators:
            logger.warning("No supported active formulas found, skipping rating calculation")
            return

        primary_formula = next(
            (formula for formula, formula_type, _ in calculators if formula_type == "elo"),
            calculators[0][0],
        )

        for formula, _, calculator in calculators:
            initial_state = calculator.get_initial_rating()
            current_states: dict[int, dict[str | None, dict[str, float]]] = defaultdict(
                dict
            )

            for contest in contests:
                blue_id = contest.id_judoka_blue
                white_id = contest.id_judoka_white
                if blue_id is None or white_id is None:
                    continue

                weight = contest.weight
                blue_state = current_states[blue_id].get(weight, initial_state.copy())
                white_state = current_states[white_id].get(weight, initial_state.copy())

                winner = contest.id_winner
                if winner == blue_id:
                    res_blue, res_white = 1.0, 0.0
                elif winner == white_id:
                    res_blue, res_white = 0.0, 1.0
                else:
                    res_blue, res_white = 0.5, 0.5

                blue_kwargs: dict[str, float] = {}
                white_kwargs: dict[str, float] = {}
                if "rating_deviation" in blue_state:
                    blue_kwargs["player_rd"] = blue_state["rating_deviation"]
                if "rating_deviation" in white_state:
                    blue_kwargs["opponent_rd"] = white_state["rating_deviation"]
                if "volatility" in blue_state:
                    blue_kwargs["player_volatility"] = blue_state["volatility"]

                if "rating_deviation" in white_state:
                    white_kwargs["player_rd"] = white_state["rating_deviation"]
                if "rating_deviation" in blue_state:
                    white_kwargs["opponent_rd"] = blue_state["rating_deviation"]
                if "volatility" in white_state:
                    white_kwargs["player_volatility"] = white_state["volatility"]

                out_blue = calculator.calculate_rating_change(
                    blue_state["rating"],
                    white_state["rating"],
                    res_blue,
                    **blue_kwargs,
                )
                out_white = calculator.calculate_rating_change(
                    white_state["rating"],
                    blue_state["rating"],
                    res_white,
                    **white_kwargs,
                )

                new_blue_state = blue_state.copy()
                new_white_state = white_state.copy()
                for key in ("rating", "rating_deviation", "volatility"):
                    if key in out_blue:
                        new_blue_state[key] = out_blue[key]
                    if key in out_white:
                        new_white_state[key] = out_white[key]

                current_states[blue_id][weight] = new_blue_state
                current_states[white_id][weight] = new_white_state

                if formula.id == primary_formula.id:
                    contest.rating_change_b = round(out_blue["rating_change"])
                    contest.rating_change_w = round(out_white["rating_change"])

                    self.session.add(
                        RatingChange(
                            id_judoka=blue_id,
                            id_contest=contest.id,
                            id_opponent=white_id,
                            opponent_rating_at_match=white_state["rating"],
                            rating_change=out_blue["rating_change"],
                            opponent_rating_change=out_white["rating_change"],
                        )
                    )
                    self.session.add(
                        RatingChange(
                            id_judoka=white_id,
                            id_contest=contest.id,
                            id_opponent=blue_id,
                            opponent_rating_at_match=blue_state["rating"],
                            rating_change=out_white["rating_change"],
                            opponent_rating_change=out_blue["rating_change"],
                        )
                    )

            for judoka_id, by_weight in current_states.items():
                for weight, state in by_weight.items():
                    self.session.add(
                        Rating(
                            id_judoka=judoka_id,
                            weight=weight,
                            formula_id=formula.id,
                            rating_value=state["rating"],
                        )
                    )

        self.session.add_all(contests)

    def _create_data_sync_record(self, created_by: UUID | None) -> DataSync:
        """Create a new DataSync record."""
        data_sync = DataSync(
            started_at=datetime.now(UTC),
            status="in_progress",
            created_by=created_by,
            sync_type="full",
        )
        self.session.add(data_sync)
        self.session.commit()
        self.session.refresh(data_sync)
        return data_sync

    def _complete_data_sync_record(
        self, data_sync: DataSync, success: bool, error_message: str | None = None
    ) -> None:
        """Complete the DataSync record with status."""
        data_sync.completed_at = datetime.now(UTC)
        data_sync.status = "completed" if success else "failed"
        data_sync.error_message = error_message
        self.session.add(data_sync)
        self.session.commit()
