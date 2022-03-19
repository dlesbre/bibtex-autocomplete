"""
Lookup for HTTPS queries
"""

from http.client import HTTPResponse, HTTPSConnection, socket  # type: ignore
from time import sleep, time
from typing import Any, Optional
from urllib.parse import urlencode

from ..utils.constants import CONNECTION_TIMEOUT, MIN_QUERY_DELAY, USER_AGENT
from ..utils.logger import logger
from .abstract_base import AbstractDataLookup

HTTP_CODE_OK = 200


class HTTPSLookup(AbstractDataLookup):
    """Abstract class to wrap https queries:
    Initialized with the entry to query info about

    Defines:
    - lookup : Self -> Optional[bytes] - performs the queries and returns raw data
    - query : Self -> Optional[BibtexEntry] - performs single query, calls lookup and handle_output

    - domain: str = "localhost" - the domain name e.g. api.crossref.org
    - host : Optional[str] = None - host when different from domain
    - path : str = "/" - the path component of the URL
    - params : dict[str, str] = {} - parameters to add to the URL

    - request : str = "GET" - https request type
    - default_headers : dict[str, str] = ... default http header
    - headers : dict[str, str] = {} - headers to add, overrite default_headers

    all of these have associated methods get_XX : Self -> Type[XX] that can be overridden
    for finer behavior control

    Virtual methods and attributes:
    - handle_output : Self, bytes -> Optional[Result] - parses output into useful result
    """

    domain: str = "localhost"
    host: Optional[str] = None
    path: str = "/"
    params: dict[str, str] = {}

    request: str = "GET"
    default_headers: dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    headers: dict[str, str] = {}

    connection_timeout: float = CONNECTION_TIMEOUT

    response: Optional[HTTPResponse] = None

    def get_headers(self) -> dict[str, str]:
        """Return the headers used in an HTTPS request"""
        headers = self.default_headers.copy()
        headers.update(self.headers)
        headers["Host"] = self.get_host()
        return headers

    def get_request(self) -> str:
        """Return the request method to use
        override this if not using self.request (default GET)"""
        return self.request

    def get_domain(self) -> str:
        """Return the path to connect to
        override this if not using self.domain"""
        return self.domain

    def get_host(self) -> str:
        """Return the host header
        override this if not using self.host or self.domain"""
        if self.host is not None:
            return self.host
        return self.get_domain()

    def get_path(self) -> str:
        """Return the path to connect to
        override this if not using self.path"""
        params = self.get_params()
        if params:
            return self.path + "?" + urlencode(params)
        return self.path

    def get_params(self) -> dict[str, str]:
        """Url parameters, can use self.entry to set them
        override this if not using self.path"""
        return self.params

    def get_body(self) -> Optional[Any]:
        """Query body, can use self.entry to set them"""
        return None

    def get_data(self) -> Optional[bytes]:
        """main lookup function
        returns true if the lookup succeeded in finding all info
        false otherwise"""
        domain = self.get_domain()
        request = self.get_request()
        path = self.get_path()
        headers = self.get_headers()
        logger.debug(
            "{request} https://{domain}{path}",
            request=request,
            domain=domain,
            path=path,
        )
        logger.verbose_debug("headers: {headers}", headers=headers)
        start = time()
        try:
            connection = HTTPSConnection(domain, timeout=self.connection_timeout)
            connection.request(
                request,
                path,
                self.get_body(),
                headers,
            )
            self.response = connection.getresponse()
            delay = round(time() - start, 3)
            if self.response.status != HTTP_CODE_OK:
                logger.warn(
                    "response: {FgYellow}{status}{reason}{FgReset} in {delay}s",
                    status=self.response.status,
                    reason=" " + self.response.reason if self.response.reason else "",
                    delay=delay,
                )
                logger.verbose_debug(
                    "response headers: {headers}", headers=self.response.headers
                )
                connection.close()
                return None
            logger.debug(
                "response: {status}{reason} in {delay}s",
                status=self.response.status,
                reason=" " + self.response.reason if self.response.reason else "",
                delay=delay,
            )
            logger.verbose_debug(
                "response headers: {headers}", headers=self.response.headers
            )
            data = self.response.read()
            connection.close()
        except socket.timeout:
            logger.warn(
                "connection timeout ({timeout}s)", timeout=self.connection_timeout
            )
            return None
        except socket.gaierror as err:
            logger.warn("connection error: {err}", err=err)
            return None
        except OSError as err:
            logger.warn("connection error: {err}", err=err)
            return None
        return data


class HTTPSRateCapedLookup(HTTPSLookup):
    """Add a rate cap to respect polite server requirements"""

    # Time of last query
    # This is a class attribute to the given lookup
    last_query_time: float = 0
    query_delay: float = MIN_QUERY_DELAY  # time between queries, in seconds

    def update_rate_cap(self) -> Optional[float]:
        """Returns the new delay between queries"""
        return None

    def get_data(self) -> Optional[bytes]:
        since_last_query = time() - self.last_query_time
        wait = self.query_delay - since_last_query
        if wait > 0.0:
            logger.debug("Rate limier: sleeping for {wait}s", wait=wait)
            sleep(wait)
        self.__class__.last_query_time = time()
        data = super().get_data()
        new_cap = self.update_rate_cap()  # update rate cap with response headers
        if new_cap is not None:
            self.__class__.query_delay = new_cap
        return data
