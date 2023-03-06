"""
Lookup for HTTPS queries
"""

from http.client import HTTPResponse, HTTPSConnection
from socket import gaierror, timeout
from ssl import _create_unverified_context
from time import sleep, time
from typing import Any, ClassVar, Dict, Optional
from urllib.parse import urlencode

from ..bibtex.normalize import normalize_url
from ..utils.constants import CONNECTION_TIMEOUT, MIN_QUERY_DELAY, USER_AGENT
from ..utils.logger import Hint, logger
from ..utils.safe_json import JSONType
from .abstract_base import AbstractDataLookup, Data, Input, Output

DNS_Fail_Hint = Hint("check your internet connection or DNS server")
SSL_Fail_Hint = Hint(
    "run 'pip install --upgrade certifi' to update certificates\n"
    "or run btac with the -S / --ignore-ssl flag."
)
TIMEOUT_Hint = Hint("you can increase timeout with -t / --timeout option.")


class HTTPSLookup(AbstractDataLookup[Input, Output]):
    """Abstract class to wrap https queries:
    Initialized with the entry to query info about

    Defines:
    - lookup : Self -> Optional[bytes] - performs the queries and returns raw data
    - query : Self -> Optional[BibtexEntry] - performs single query, calls lookup and handle_output

    - domain: str = "localhost" - the domain name e.g. api.crossref.org
    - host : Optional[str] = None - host when different from domain
    - path : str = "/" - the path component of the URL
    - params : Dict[str, str] = {} - parameters to add to the URL

    - request : str = "GET" - https request type
    - default_headers : Dict[str, str] = ... default http header
    - headers : Dict[str, str] = {} - headers to add, overrite default_headers

    all of these have associated methods get_XX : Self -> Type[XX] that can be overridden
    for finer behavior control

    Virtual methods and attributes:
    - handle_output : Self, bytes -> Optional[Result] - parses output into useful result
    """

    domain: str = "localhost"
    host: Optional[str] = None
    path: str = "/"
    params: Dict[str, str] = {}

    ignore_ssl: ClassVar[bool] = False
    silent_fail: ClassVar[bool] = False

    # Safe parameters kept in urlencode
    safe: str = ""

    request: str = "GET"
    accept: str = "application/json"
    default_headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
    }
    headers: Dict[str, str] = {}

    connection_timeout: Optional[float] = CONNECTION_TIMEOUT

    response: Optional[HTTPResponse] = None

    _last_query_info: Dict[str, JSONType] = {}

    def get_headers(self) -> Dict[str, str]:
        """Return the headers used in an HTTPS request"""
        headers = self.default_headers.copy()
        headers["Accept"] = self.accept
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
            return self.path + "?" + urlencode(params, safe=self.safe)
        return self.path

    def get_params(self) -> Dict[str, str]:
        """Url parameters, can use self.entry to set them
        override this if not using self.path"""
        return self.params

    def get_body(self) -> Optional[Any]:
        """Query body, can use self.entry to set them"""
        return None

    def get_data(self) -> Optional[Data]:
        """main lookup function
        returns true if the lookup succeeded in finding all info
        false otherwise"""
        domain = self.get_domain()
        request = self.get_request()
        path = self.get_path()
        headers = self.get_headers()
        url = f"https://{domain}{path}"
        self._last_query_info = dict()
        logger.debug(
            "{request} {url}",
            request=request,
            url=url,
        )
        logger.very_verbose_debug("headers: {headers}", headers=headers)
        start = time()
        try:
            if self.ignore_ssl:
                connection = HTTPSConnection(
                    domain,
                    timeout=self.connection_timeout,
                    context=_create_unverified_context(),
                )
            else:
                connection = HTTPSConnection(domain, timeout=self.connection_timeout)
            connection.request(
                request,
                path,
                self.get_body(),
                headers,
            )
            self.response = connection.getresponse()
            delay = round(time() - start, 3)
            self._last_query_info = {
                "url": url,
                "response-time": delay,
                "response-status": self.response.status,
            }
            logger.debug(
                "response {status}{reason} in {delay}s",
                status=self.response.status,
                reason=" " + self.response.reason if self.response.reason else "",
                delay=delay,
            )
            logger.very_verbose_debug(
                "response headers: {headers}", headers=self.response.headers
            )
            data = self.response.read()
            connection.close()
        except timeout:
            if self.silent_fail:
                return None
            logger.warn(
                "connection timeout ({timeout}s)", timeout=self.connection_timeout
            )
            TIMEOUT_Hint.emit()
            return None
        except gaierror as err:
            if self.silent_fail:
                return None
            error_name = "CONNECTION ERROR"
            error_msg = "{err}"
            hint = None
            if str(err) == "[Errno -3] Temporary failure in name resolution":
                padding = "\n" + " " * (len(error_name) + 2)
                error_msg += "{}Could not resolve '{}'".format(padding, domain)
                hint = DNS_Fail_Hint
            elif "[SSL: CERTIFICATE_VERIFY_FAILED]" in str(err):
                hint = SSL_Fail_Hint
            logger.warn(error_msg, err=err, error=error_name)
            if hint is not None:
                hint.emit()
            return None
        except OSError as err:
            if self.silent_fail:
                return None
            logger.warn("{err}", err=err, error="CONNECTION ERROR")
            return None
        return Data(
            data=data,
            code=self.response.status,
            delay=delay,
            reason=self.response.reason,
        )

    def get_last_query_info(self) -> Dict[str, JSONType]:
        base = super().get_last_query_info()
        base.update(self._last_query_info)
        return base


class RedirectFollower(HTTPSLookup[Input, Output]):
    """Follows redirection up to max_depth
    returns final data
    Only works with fixed attributes for domain/path/query..."""

    max_depth = 10
    depth = 0

    def get_data(self) -> Optional[Data]:
        data = super().get_data()
        while data is not None and data.code in [301, 302, 303]:
            if self.response is None:
                return data
            location = self.response.getheader("Location")
            if location is None:
                return data
            self.depth += 1
            logger.debug("Redirect {depth} to : {url}", depth=self.depth, url=location)
            if self.depth >= self.max_depth:
                logger.warn("Redirection depth exceeded")
                return None
            split = normalize_url(location)
            if split is None:
                return data
            self.domain = split[0]
            self.path = split[1]
            data = super().get_data()
        return data


class HTTPSRateCapedLookup(HTTPSLookup[Input, Output]):
    """Add a rate cap to respect polite server requirements"""

    # Time of last query
    # This is a class attribute to the given lookup
    last_query_time: float = 0
    query_delay: float = MIN_QUERY_DELAY  # time between queries, in seconds

    def update_rate_cap(self) -> Optional[float]:
        """Returns the new delay between queries"""
        return None

    def get_data(self) -> Optional[Data]:
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
