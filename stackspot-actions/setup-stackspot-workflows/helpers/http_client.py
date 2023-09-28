import logging
import requests
from typing import Callable


class HttpClient:
    def _call(
        self,
        method: Callable,
        url: str,
        title: str = str(),
        raise_for_status: bool = False,
        **kwargs
    ) -> requests.Response:
        logging.info(f"{'-'*(28 - int(len(title)/2))}[ {title} ]{'-'*(28 - int(len(title)/2))}")
        logging.info(f"[{method.__name__.upper()}] {url}")
        # logging.info(f"Headers: {kwargs.get('headers')}")
        resp = method(url, verify=False, **kwargs)
        logging.info(f"Response status code: {resp.status_code}")
        if raise_for_status and not resp.ok:
            logging.info(f"Request body: {kwargs.get('json')}")
            logging.info(f"Response body: {resp.text}")
        if resp.ok or not raise_for_status:
            logging.info(f"{'-'*25}[ SUCCESS ]{'-'*25}")
        else:
            logging.info(f"{'-'*25}[ FAILURE ]{'-'*25}")
        raise_for_status and resp.raise_for_status()
        return resp

    def post(self, **kwargs):
        return self._call(requests.post, **kwargs)

    def get(self, **kwargs):
        return self._call(requests.get, **kwargs)

    def patch(self, **kwargs):
        return self._call(requests.patch, **kwargs)

    def put(self, **kwargs):
        return self._call(requests.put, **kwargs)
