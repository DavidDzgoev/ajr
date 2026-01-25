"""Service for interacting with judobase API."""

import logging
from typing import Any

from judobase import JudoBase
from judobase.schemas import WeightEnum, Competition, CountryShort, Judoka, Contest
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class JudobaseService:
    """Service for fetching data from judobase API."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.api: JudoBase | None = None

    async def __aenter__(self) -> "JudobaseService":
        """Async context manager entry."""
        self.api = JudoBase()
        await self.api.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.api:
            await self.api.__aexit__(exc_type, exc_val, exc_tb)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_all_competitions(self) -> list[Competition]:
        """
        Get all competitions from judobase.

        Returns:
            List of Competition objects from judobase.
        """
        self.check_api_initialized()

        logger.info("Fetching all competitions from judobase")
        competitions = await self.api.all_competition()
        logger.info(f"Fetched {len(competitions)} competitions")
        return competitions

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_all_countries(self) -> list[CountryShort]:
        """
        Get all countries from judobase.

        Returns:
            List of Country objects from judobase.
        """
        self.check_api_initialized()

        logger.info("Fetching all countries from judobase")
        countries = await self.api.get_country_list()
        logger.info(f"Fetched {len(countries)} countries")
        return countries

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_judoka_by_id(self, judoka_id: str) -> tuple[Judoka | None, str]:
        """
        Get a specific judoka by ID.

        Args:
            judoka_id: The judobase competition ID.

        Returns:
            Judoka object from judobase.
        """
        self.check_api_initialized()

        logger.debug(f"Fetching judoka {judoka_id} from judobase")
        try:
            judoka = await self.api.get_judoka_info(judoka_id)
        except ValidationError as e:
            logger.warning("Judoka %s skipped due to validation error: %s", judoka_id, e)
            judoka = None
        return judoka, judoka_id

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_contests_by_competition_id(
        self,
        competition_id: int,
        weight: WeightEnum | None = None,
        include_events: bool = False,
    ) -> list[Contest]:
        """
        Get contests for a specific competition.

        Args:
            competition_id: The judobase competition ID.
            weight: Optional weight category filter.
            include_events: Whether to include event details.

        Returns:
            List of Contest objects from judobase.
        """
        self.check_api_initialized()

        logger.info(
            f"Fetching contests for competition {competition_id} "
            f"(weight={weight}, include_events={include_events})"
        )
        contests = await self.api.contests_by_competition_id(
            competition_id=competition_id,
            weight=weight,
            include_events=include_events,
        )
        logger.info(f"Fetched {len(contests)} contests")
        return contests

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_all_contests(self) -> list[Any]:
        """
        Get all contests from judobase.

        Returns:
            List of all Contest objects from judobase.
        """
        self.check_api_initialized()

        logger.info("Fetching all contests from judobase")
        contests = await self.api.all_contests()
        logger.info(f"Fetched {len(contests)} contests")
        return contests

    def check_api_initialized(self) -> None:
        """Check if the JudoBase API is initialized."""
        if not self.api:
            raise RuntimeError("JudoBase API not initialized. Use async context manager.")
