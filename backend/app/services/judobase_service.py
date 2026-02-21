"""Service for interacting with judobase API."""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Coroutine

from aiohttp import ClientError
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
AsyncMethod = Callable[..., Coroutine[Any, Any, Any]]


retry_policy = retry(
    retry=retry_if_exception_type((ClientError, TimeoutError, asyncio.TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)


def requires_initialized_api(func: AsyncMethod) -> AsyncMethod:
    """Ensure API client is initialized before calling service method."""

    @wraps(func)
    async def wrapper(
        self: "JudobaseService", *args: Any, **kwargs: Any
    ) -> Any:
        self.check_api_initialized()
        return await func(self, *args, **kwargs)

    return wrapper


def call_policy(func: AsyncMethod) -> AsyncMethod:
    """Apply API initialization guard and retry policy together."""

    return retry_policy(requires_initialized_api(func))


class JudobaseService:
    """Service for fetching data from judobase API."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.api: JudoBase | None = None

    async def __aenter__(self) -> "JudobaseService":
        """Async context manager entry."""
        self.api = JudoBase()  # type: ignore[no-untyped-call]
        await self.api.__aenter__()  # type: ignore[no-untyped-call]
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.api:
            await self.api.__aexit__(exc_type, exc_val, exc_tb)  # type: ignore[no-untyped-call]
            self.api = None

    @call_policy
    async def get_all_competitions(self) -> list[Competition]:
        """
        Get all competitions from judobase.

        Returns:
            List of Competition objects from judobase.
        """
        api = self._get_api()

        logger.info("Fetching all competitions from judobase")
        competitions = await api.all_competition()
        logger.info(f"Fetched {len(competitions)} competitions")
        return competitions

    @call_policy
    async def get_all_countries(self) -> list[CountryShort]:
        """
        Get all countries from judobase.

        Returns:
            List of Country objects from judobase.
        """
        api = self._get_api()

        logger.info("Fetching all countries from judobase")
        countries = await api.get_country_list()
        logger.info(f"Fetched {len(countries)} countries")
        return countries

    @call_policy
    async def get_judoka_by_id(self, judoka_id: str) -> tuple[Judoka | None, str]:
        """
        Get a specific judoka by ID.

        Args:
            judoka_id: The judobase judoka ID.

        Returns:
            Judoka object from judobase.
        """
        api = self._get_api()

        logger.debug(f"Fetching judoka {judoka_id} from judobase")
        try:
            judoka = await api.get_judoka_info(judoka_id)
        except ValidationError as e:
            logger.warning(
                "Judoka %s skipped due to validation error: %s", judoka_id, e
            )
            judoka = None
        return judoka, judoka_id

    @call_policy
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
        api = self._get_api()

        logger.info(
            f"Fetching contests for competition {competition_id} "
            f"(weight={weight}, include_events={include_events})"
        )
        contests = await api.contests_by_competition_id(
            competition_id=competition_id,
            weight=weight,
            include_events=include_events,
        )
        logger.info(f"Fetched {len(contests)} contests")
        return contests

    @call_policy
    async def get_all_contests(self) -> list[Contest]:
        """
        Get all contests from judobase.

        Returns:
            List of all Contest objects from judobase.
        """
        api = self._get_api()

        logger.info("Fetching all contests from judobase")
        contests = await api.all_contests()
        logger.info(f"Fetched {len(contests)} contests")
        return contests

    def check_api_initialized(self) -> None:
        """Check if the JudoBase API is initialized."""
        if not self.api:
            raise RuntimeError(
                "JudoBase API not initialized. Use async context manager."
            )

    def _get_api(self) -> JudoBase:
        self.check_api_initialized()
        assert self.api is not None
        return self.api
