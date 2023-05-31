# LangChainL402

LangChainL402 is a Python project that enables users of the `requests` package
to easily navigate APIs that require
[L402](https://docs.lightning.engineering/the-lightning-network/l402) based
authentication. This project also includes a LangChain APIChain compatible
wrapper that enables LangChain agents to interact with APIs that require L402
for payment or authentication. This enables agents to access real-world
resources behind a Lightning metered API.


## Features
- Provides a wrapper around `requests` library to handle LSATs and Lightning
  payments.

- Easily integrates with APIs requiring L402-based authentication.

- Designed to operate seamlessly with LND (Lightning Network Daemon).

- Enables LangChain Agents traverse APIs that require L402 authentication
  within an API Chain


## Installation

To install the LangChainL402 project, you can clone the repository directly
from GitHub:

```bash
git clone https://github.com/yourusername/LangChainL402.git
cd LangChainL402

Please ensure you have all the necessary Python dependencies installed. You can
install them using pip:
```
pip install -r requirements.txt
```

## Usage

This project provides classes to handle Lightning payments (e.g., `LndNode`,
`LightningNode`) and to manage HTTP requests with L402-based authentication
(`RequestsL402Wrapper`, `ResponseTextWrapper`).

First, initialize the LndNode with your Lightning node's details. Then, you can
use the `RequestsL402Wrapper` to send HTTP requests to an API that requires
L402-based authentication. If the server responds with a 402 Payment Required
status code, the library will automatically handle the payment and retry the
request.

Here is a basic example:
```
import requests

from lightning import LndNode
from requests_l402 import RequestsL402Wrapper, ResponseTextWrapper

from langchain.chains import APIChain
from langchain.prompts.prompt import PromptTemplate

from langchain.llms import OpenAI

# Initialize LndNode
lnd_node = LndNode(
    cert_path='path/to/tls.cert',
    macaroon_path='path/to/admin.macaroon',
    host='localhost',
    port=10018
)

# Initialize RequestsL402Wrapper
requests_L402 = RequestsL402Wrapper(lnd_node, requests)
lang_chain_request_L402 = ResponseTextWrapper(requests_L402)

# Now you can use lang_chain_request_L402 to send HTTP requests and have the
# L402 aspect (if needed) handled behind the scenes.
response = lang_chain_request_L402.get('http://api.example.com')

# You can also use this with an API Chain instance like so:
llm = OpenAI(temperature=0)
chain_new = APIChain.from_llm_and_api_docs(llm, API_DOCS, verbose=True)

# Swap our the default wrapper with our L402 aware wrapper.
chain_new.requests_wrapper = lang_chain_request_L402

output = chain_new.run('LLM query here')
print(output)
```
