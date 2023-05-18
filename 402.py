import base64
import re
import binascii
from typing import Tuple, Union
from http.client import HTTPMessage
from pymacaroons import Macaroon

import base64
import re

from contextlib import suppress

from threading import Lock
 
import time
from contextlib import suppress

from pymacaroons import Macaroon
from datetime import datetime
import struct
import hashlib

import requests

import lightning_pb2 as ln
import lightning_pb2_grpc as lnrpc

import grpc
import os

import codecs


# Due to updated ECDSA generated tls.cert we need to let gprc know that
# we need to use that cipher suite otherwise there will be a handhsake
# error when we communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

# Constants
HEADER_AUTHORIZATION = "Authorization"
HEADER_MACAROON_MD = "Grpc-Metadata-Macaroon"
HEADER_MACAROON = "Macaroon"

AUTH_HEADER = "WWW-Authenticate"

auth_regex = re.compile(r"LSAT (.*?):([a-f0-9]{64})")
auth_format = "LSAT %s:%s"

def make_lnd_conn():
    # Lnd cert is at ~/.lnd/tls.cert on Linux and
    # ~/Library/Application Support/Lnd/tls.cert on Mac
    cert = open(os.path.expanduser('~/gocode/src/github.com/lightningnetwork/lnd/test_lnd2/tls.cert'), 'rb').read()
    cert_creds = grpc.ssl_channel_credentials(cert)

    with open(os.path.expanduser('~/gocode/src/github.com/lightningnetwork/lnd/test_lnd2/data/chain/bitcoin/simnet/admin.macaroon'), 'rb') as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, 'hex')

    def metadata_callback(context, callback):
        # for more info see grpc docs
        callback([('macaroon', macaroon)], None)

    # now build meta data credentials
    auth_creds = grpc.metadata_call_credentials(metadata_callback)

    # combine the cert credentials and the macaroon auth credentials
    # such that every call is properly encrypted and authenticated
    combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)

    # finally pass in the combined credentials when creating a channel
    channel = grpc.secure_channel('localhost:10018', combined_creds)
    stub = lnrpc.LightningStub(channel)

    return stub

def pay_invoice(invoice):
    lnd_node = make_lnd_conn()

    pay_resp = lnd_node.SendPaymentSync(ln.SendRequest(payment_request=invoice))
    print(pay_resp)

    pre_image = binascii.hexlify(pay_resp.payment_preimage).decode('utf-8')
    print("preimage: ", pre_image)

    return pre_image

class L402RequestsWrapper(object):
    def get(self, url):
        return request_L402(url)

def request_L402(url, headers=None):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            print('Request successful!')
            print('Response:', response.text)
        else:
            if response.status_code == 402:
                auth_header = response.headers.get(AUTH_HEADER)
                if auth_header:
                    print('Error L402: Authentication Required')
                    print('WWW-Authenticate:', auth_header)
                else:
                    print('Request failed with status code:', response.status_code)

                print(auth_header)

                # Extract macaroon value
                macaroon = re.search(r'macaroon="(.*?)"', auth_header).group(1)

                # Extract invoice value
                invoice = re.search(r'invoice="(.*?)"', auth_header).group(1)

                print("Macaroon:", macaroon)
                print("Invoice:", invoice)

                pre_image = pay_invoice(invoice)

                headers = {
                    'Authorization': f'LSAT {macaroon}:{pre_image}'
                }

                # try the response again with the proper headers
                response = requests.get(url, headers=headers)


                # Check the response status code for success
                if response.status_code == 200:
                    #print('Request successful!')
                    #print('Response:', response.text)

                    return response.text
                else:
                    print('Request failed with status code:', response.status_code)

            else:
                print('Request failed with status code:', response.status_code)

    except requests.exceptions.RequestException as e:
        print('Request failed:', e)

API_DOCS ='''BASE URL: http://localhost:8085

API Documentation
The API endpoint /v1/models HTTP endpoint can be used to fetch the set of supported models. The response is text, the list of models separated by a comma

Request:
there are no query params for the API

Response: 
The set of models supported as a list, with commas between the entries

an example response is: The set of models supported are: gpt4, gpt9, gpt5

in this response, there are 3 supported models: gpt4, gpt9, and gpt5
'''

if __name__ == "__main__":
    url = 'http://localhost:8085/v1'

    #wrapper = L402RequestsWrapper()
    #wrapper.get(url)

    from langchain.chains import APIChain
    from langchain.prompts.prompt import PromptTemplate

    from langchain.llms import OpenAI

    llm = OpenAI(temperature=0)

    chain_new = APIChain.from_llm_and_api_docs(llm, API_DOCS, verbose=True)

    chain_new.requests_wrapper = L402RequestsWrapper()

    chain_new.run('which models are supported?')
