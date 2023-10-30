import logging
import requests

from provider.errors import NotFoundError, UnauthorizedError


def handle_api_response_errors(response: requests.Response, log_error: bool = True) -> bool:
    if response.ok:
        return True
    if log_error:
        logging.error("Error response body: %s", response.text)
    match response.status_code:
        case requests.codes.not_found:
            raise NotFoundError()
        case requests.codes.unauthorized:
            raise UnauthorizedError()
    response.raise_for_status()
