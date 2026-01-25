"""Service for synchronizing data from judobase."""
import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session

from app.models import (
    Competition,
    DataSync,
    Country,
    Contest,
    Judoka,
)
from app.services.judobase_service import JudobaseService

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing data from judobase to database."""

    def __init__(self, session: Session) -> None:
        self.session = session

    async def sync_all(self, created_by: UUID | None = None) -> DataSync:
        """Synchronize all data from judobase and calculate ratings."""
        data_sync = self._create_data_sync_record(created_by)

        try:
            async with JudobaseService() as judobase:
                await self._download_countries(judobase, data_sync)
                await self._download_competitions(judobase, data_sync)
                await self._download_contests_and_judokas(judobase, data_sync)

            self._complete_data_sync_record(data_sync, True)
            logger.info(
                f"Sync completed: {data_sync.records_processed} processed, "
                f"{data_sync.records_created} created, {data_sync.records_updated} updated"
            )

        except Exception as e:
            logger.error(f"Sync failed: {str(e)}", exc_info=True)
            self._complete_data_sync_record(data_sync, False, str(e))

        return data_sync

    async def _download_contests_and_judokas(self, judobase: JudobaseService, data_sync: DataSync) -> None:
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
            blue_ok = contest.id_person_blue is None or contest.id_person_blue in saved_judoka_ids
            white_ok = contest.id_person_white is None or contest.id_person_white in saved_judoka_ids
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

    async def _download_countries(self, judobase: JudobaseService, data_sync: DataSync) -> None:
        """Download countries from judobase and store in database."""
        logger.info("Downloading countries")
        countries = await judobase.get_all_countries()

        for country in countries:
            country_record =Country(
                id=country.id_country,
                name=country.name,
                ioc=country.ioc,
            )
            self.session.add(country_record)
            data_sync.records_created += 1

    async def _download_competitions(self, judobase: JudobaseService, data_sync: DataSync) -> None:
        """Download competitions from judobase and store in database."""
        logger.info("Downloading competitions")
        competitions = await judobase.get_all_competitions()

        for competition in competitions:
            competition_record =Competition(
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

    def _complete_data_sync_record(self, data_sync: DataSync, success: bool, error_message: str | None = None) -> None:
        """Complete the DataSync record with status."""
        data_sync.completed_at = datetime.now(UTC)
        data_sync.status = "completed" if success else "failed"
        data_sync.error_message = error_message
        self.session.add(data_sync)
        self.session.commit()
