from unify import Unify, AsyncUnify
from unify.utils import _validate_api_key
from unify.exceptions import UnifyError
from typing import Optional, Union, List, Tuple, Dict, Iterable


class MultiLLM:

    def __init__(
            self,
            endpoints: Optional[Iterable[str]] = None,
            asynchronous: bool = False,
            api_key: Optional[str] = None,
    ) -> None:
        endpoints = list(endpoints)
        self._api_key = _validate_api_key(api_key)
        self._endpoints = endpoints
        self._client_class = AsyncUnify if asynchronous else Unify
        self._clients = self._create_clients(endpoints)

    def _create_clients(self, endpoints: List[str]) -> Dict[str, Union[Unify, AsyncUnify]]:
        return {endpoint: self._client_class(endpoint, api_key=self._api_key) for endpoint in endpoints}

    def add_endpoints(self, endpoints: Union[List[str], str], ignore_duplicates: bool = True) -> None:
        if isinstance(endpoints, str):
            endpoints = [endpoints]
        # remove duplicates
        if ignore_duplicates:
            endpoints = [endpoint for endpoint in endpoints if endpoint not in self._endpoints]
        elif len(self._endpoints + endpoints) != len(set(self._endpoints + endpoints)):
            raise UnifyError("at least one of the provided endpoints to add {}"
                             "was already set present in the endpoints {}."
                             "Set ignore_duplicates to True to ignore errors like this".format(endpoints,
                                                                                               self._endpoints))
        # update endpoints
        self._endpoints = self._endpoints + endpoints
        # create new clients
        self._clients.update(self._create_clients(endpoints))

    def remove_endpoints(self, endpoints: Union[List[str], str], ignore_missing: bool = True) -> None:
        if isinstance(endpoints, str):
            endpoints = [endpoints]
        # remove irrelevant
        if ignore_missing:
            endpoints = [endpoint for endpoint in endpoints if endpoint in self._endpoints]
        elif len(self._endpoints) != len(set(self._endpoints + endpoints)):
            raise UnifyError("at least one of the provided endpoints to remove {}"
                             "was not present in the current endpoints {}."
                             "Set ignore_missing to True to ignore errors like this".format(endpoints,
                                                                                            self._endpoints))
        # update endpoints and clients
        for endpoint in endpoints:
            self._endpoints.remove(endpoint)
            del self._clients[endpoint]

    @property
    def endpoints(self) -> Tuple[str]:
        return tuple(self._endpoints)

    @property
    def clients(self) -> Dict[str, Union[Unify, AsyncUnify]]:
        return self._clients
