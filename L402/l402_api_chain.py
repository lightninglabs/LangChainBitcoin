import requests

from typing import Any, Dict, Optional
from langchain.chains.api.prompt import API_RESPONSE_PROMPT, API_URL_PROMPT
from langchain.chains import APIChain
from langchain.prompts import BasePromptTemplate
from langchain.base_language import BaseLanguageModel
from langchain.chains.llm import LLMChain

from .requests_l402 import RequestsL402Wrapper
from .requests_l402 import ResponseTextWrapper

from lightning import LightningNode

class L402APIChain(APIChain):
    requests_wrapper: Any

    @classmethod
    def from_llm_and_api_docs(
        cls,
        llm: BaseLanguageModel,
        api_docs: str,
        headers: Optional[dict] = None,
        api_url_prompt: BasePromptTemplate = API_URL_PROMPT,
        api_response_prompt: BasePromptTemplate = API_RESPONSE_PROMPT,
        lightning_node = None,
        **kwargs: Any,
    ) -> APIChain:
        """Load chain from just an LLM and the api docs."""

        requests_L402 = RequestsL402Wrapper(lightning_node, requests)
        lang_chain_request_L402 = ResponseTextWrapper(
                requests_wrapper=requests_L402,
        )

        get_request_chain = LLMChain(llm=llm, prompt=api_url_prompt)
        get_answer_chain = LLMChain(llm=llm, prompt=api_response_prompt)

        return cls(
            api_request_chain=get_request_chain,
            api_answer_chain=get_answer_chain,
            requests_wrapper=lang_chain_request_L402,
            api_docs=api_docs,
            **kwargs,
        )
