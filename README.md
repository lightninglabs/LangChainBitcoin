# LangChainBitcoin

`LangChainBitcoin` is a suite of tools that enables `langchain` agents to
directly interact with Bitcoin and also the Lightning Network. This package has
two main features:
  
  * **LLM Agent BitcoinTools**: Using the newly available Open AP GPT-3/4
    function calls and the built in set of abstractions for tools in
    `langchain`, users can create agents that are capaable of holding Bitcoin
    balance (on-chain and on LN), sending/receiving Bitcoin on LN, and also
    generally interacting with a Lightning node (lnd).

  * **L402 HTTP API Traversal**: LangChainL402 is a Python project that enables
    users of the `requests` package to easily navigate APIs that require
    [L402](https://docs.lightning.engineering/the-lightning-network/l402) based
    authentication. This project also includes a LangChain APIChain compatible
    wrapper that enables LangChain agents to interact with APIs that require
    L402 for payment or authentication. This enables agents to access
    real-world resources behind a Lightning metered API.


## Features
- Provides a wrapper around `requests` library to handle LSATs and Lightning
  payments.

- Easily integrates with APIs requiring L402-based authentication.

- Designed to operate seamlessly with LND (Lightning Network Daemon).

- Enables LangChain Agents traverse APIs that require L402 authentication
  within an API Chain.

- Generic set of Bitcoin tools giving agents the ability to hold and use the
  Internet's native currency.



## Installation

To install the LangChainL402 project, you can clone the repository directly
from GitHub:

```bash
git clone https://github.com/lightninglabs/LangChainBitcoin.git
cd LangChainBitcoin
```

Please ensure you have all the necessary Python dependencies installed. You can
install them using pip:
```
pip install -r requirements.txt
```

## Usage

### LLM Agent Bitcoin Tools

Check out the contained Jupyter notebook for an interactive example you can
run/remix: [LLM Bitcoin Tools](llm_bitcoin_tools.ipynb).

### L402 API Traversal

This project provides classes to handle Lightning payments (e.g., `LndNode`,
`LightningNode`) and to manage HTTP requests with L402-based authentication
(`RequestsL402Wrapper`, `ResponseTextWrapper`).

First, initialize the `LndNode` with your Lightning node's details. Then, you
can use the modified `L402APIChain` wrapper around the normal `APIChain` class
to instantiate an L402-aware API Chain. If the server responds with a 402
Payment Required status code, the library will automatically handle the payment
and retry the request.

Here is a basic example:
```python
import requests

from lightning import LndNode

from l402_api_chain import L402APIChain
from langchain.llms import OpenAI

# Initialize LndNode
lnd_node = LndNode(
    cert_path='path/to/tls.cert',
    macaroon_path='path/to/admin.macaroon',
    host='localhost',
    port=10018
)

# You can also use this with an API Chain instance like so:
llm = OpenAI(temperature=0)
chain_new = L402APIChain.from_llm_and_api_docs(
        llm, API_DOCS, lightning_node=lnd_node, verbose=True,
)

# Swap our the default wrapper with our L402 aware wrapper.
chain_new.requests_wrapper = lang_chain_request_L402

output = chain_new.run('LLM query here')
print(output)
```
