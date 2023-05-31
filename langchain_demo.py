from lightning import LndNode

from requests_l402 import RequestsL402Wrapper
from requests_l402 import ResponseTextWrapper

import requests

API_DOCS ='''BASE URL: http://localhost:8085

API Documentation
The API endpoint /v1/models HTTP endpoint can be used to fetch the set of supported models. The response is text, the list of models separated by a comma

Request:
There are no query params for the API

Response: 
A JSON object of the set of supported models, which looks similar to:
{
  "models": [
    {
      "id": "gpt9",
      "name": "GPT-9",
      "version": "1.0"
    },
    {
      "id": "gpt88",
      "name": "GPT-88",
      "version": "1.0"
    },
    {
      "id": "gptgammaz",
      "name": "GPT-Gammaz",
      "version": "1.0"
    }
  ]
}

'''

if __name__ == "__main__":
    url = 'http://localhost:8085/v1'

    from langchain.chains import APIChain
    from langchain.prompts.prompt import PromptTemplate

    from langchain.llms import OpenAI

    lnd_node = LndNode(
        cert_path='~/gocode/src/github.com/lightningnetwork/lnd/test_lnd2/tls.cert',
        macaroon_path='~/gocode/src/github.com/lightningnetwork/lnd/test_lnd2/data/chain/bitcoin/simnet/admin.macaroon',
        host='localhost',
        port=10018
    )

    requests_L402 = RequestsL402Wrapper(lnd_node, requests)
    lang_chain_request_L402 = ResponseTextWrapper(requests_L402)

    llm = OpenAI(temperature=0)

    chain_new = APIChain.from_llm_and_api_docs(llm, API_DOCS, verbose=True)

    chain_new.requests_wrapper = lang_chain_request_L402

    output = chain_new.run('how many total models are supported?')
    print(output)

    output = chain_new.run('which models are supported?')
    print(output)
