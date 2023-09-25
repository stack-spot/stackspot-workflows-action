import logging
import requests
from typing import Callable


class HttpClient:
    def _call(self, method: Callable, url: str, **kwargs) -> requests.Response:
        logging.info(f"URL: {url}")
        # logging.info(f"Headers: {kwargs.get('headers')}")
        resp = method(url, verify=False, **kwargs)
        logging.info(f"Response status code: {resp.status_code}")
        logging.info("--------------------------------------------------------------------")
        # logging.info(f"Response body: {resp.text}")
        return resp

    def post(self, **kwargs):
        logging.info("----------------------------[ POST ]--------------------------------")
        return self._call(requests.post, **kwargs)

    def get(self, **kwargs):
        logging.info("----------------------------[ GET ]---------------------------------")
        return self._call(requests.get, **kwargs)

    def patch(self, **kwargs):
        logging.info("----------------------------[ PATCH ]-------------------------------")
        return self._call(requests.patch, **kwargs)
