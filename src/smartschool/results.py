from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import count

from .exceptions import SmartSchoolDownloadError
from .objects import ResultWithDetails, ResultWithoutDetails

__all__ = ["ResultDetail", "Results"]

from .session import SessionMixin

RESULTS_PER_PAGE = 50


@dataclass
class Results(SessionMixin, Iterable[ResultWithoutDetails]):
    """
    Interfaces with the evaluations of smartschool.

    To reproduce: "Ga naar" > "Resultaten", it'll be one of the XHR calls then.

    Example:
    -------
    >>> for result in Results():
    >>>     print(result.name)
    Repetitie hoofdstuk 1

    """

    def __iter__(self) -> Iterator[ResultWithoutDetails]:
        last_component = None
        for page_nr in count(start=1):  # pragma: no branch
            downloaded_webpage = self.session.get(f"/results/api/v1/evaluations/?pageNumber={page_nr}&itemsOnPage={RESULTS_PER_PAGE}")
            if not downloaded_webpage or not downloaded_webpage.content:
                raise SmartSchoolDownloadError("No JSON was returned for the results?!")

            json = downloaded_webpage.json()
            for result in json:
                component = result.get("component")
                if component is not None:
                    last_component = component
                else:
                    result["component"] = last_component
                    
                if result["graphic"]["value"] == "—":
                    result["graphic"]["value"] = -1
                    result["graphic"]["type"] = "percentage"
                    
                yield ResultWithoutDetails(**result)

            if len(json) < RESULTS_PER_PAGE:
                break


@dataclass
class ResultDetail(SessionMixin):
    result_id: str

    def get(self) -> ResultWithDetails:
        downloaded_webpage = self.session.get(f"/results/api/v1/evaluations/{self.result_id}")
        if not downloaded_webpage or not downloaded_webpage.content:
            raise SmartSchoolDownloadError("No JSON was returned for the details?!")

        json = downloaded_webpage.json()
        return ResultWithDetails(**json)
