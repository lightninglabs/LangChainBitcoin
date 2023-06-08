from pydantic import BaseModel

from typing import Any

import requests
import re

L402_ERROR_CODE = 402

AUTH_HEADER = "WWW-Authenticate"

class RequestsL402Wrapper(object):
    """
    """

    def __init__(self, lnd_node, requests):
        self.lnd_node = lnd_node
        self.requests = requests

    def _L402_auth(self, response):
        auth_header = response.headers.get(AUTH_HEADER)

        # Extract macaroon value
        macaroon = re.search(r'macaroon="(.*?)"', auth_header).group(1)

        # Extract invoice value
        invoice = re.search(r'invoice="(.*?)"', auth_header).group(1)

        print("Paying invoice: ", invoice)

        pre_image = self.lnd_node.pay_invoice(invoice)

        print("Obtained preimage: ", pre_image)

        headers = {
            'Authorization': 'LSAT {macaroon}:{pre_image}'.format(
                macaroon=macaroon, pre_image=pre_image,
            ),
        }

        print("Assembling final authorization header: ", headers)

        return headers

    def _L402(func):
        def wrapper(self, *args, **kwargs):
            requests_func = getattr(self.requests, func.__name__)

            response = requests_func(*args, **kwargs)

            if response.status_code != L402_ERROR_CODE:
                return response

            print("L402 error path={path}, attempting to pay invoice and retry request...".format(path=args[0]))

            L402_auth_header = self._L402_auth(response)

            kwargs.setdefault('headers', {})
            kwargs['headers'].update(L402_auth_header)

            return requests_func(*args, **kwargs)
        return wrapper

    # TODO(roasbeef): should also be able to set the set of headers, etc

    @_L402
    def get(self, url, **kwargs):
        return

    @_L402
    def post(self, url, data=None, json=None, **kwargs):
        return

    @_L402
    def put(self, url, data=None, **kwargs):
        return

    @_L402
    def delete(self, url, **kwargs):
        return

    @_L402
    def head(self, url, **kwargs):
        return

    @_L402
    def patch(self, url, data=None, **kwargs):
        return

class ResponseTextWrapper(BaseModel):
    requests_wrapper: Any

    @staticmethod
    def response_text(func):
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            return response.text
        return wrapper

    @response_text
    def get(self, url, **kwargs):
        return self.requests_wrapper.get(url, **kwargs)

    @response_text
    def post(self, url, data=None, json=None, **kwargs):
        return self.requests_wrapper.post(url, data, json, **kwargs)

    @response_text
    def put(self, url, data=None, **kwargs):
        return self.requests_wrapper.put(url, data, **kwargs)

    @response_text
    def delete(self, url, **kwargs):
        return self.requests_wrapper.delete(url, **kwargs)

    @response_text
    def head(self, url, **kwargs):
        return self.requests_wrapper.head(url, **kwargs)

    @response_text
    def patch(self, url, data=None, **kwargs):
        return self.requests_wrapper.patch(url, data, **kwargs)
