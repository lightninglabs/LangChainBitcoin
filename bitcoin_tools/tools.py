from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.tools import BaseTool, tool

from protos import lightning_pb2 as ln

from lightning import LndNode

from typing import List


class LndTools(BaseToolkit):
    class Config:
        arbitrary_types_allowed = True

    lnd_node: LndNode

    @classmethod
    def from_lnd_node(cls, lnd_node: LndNode) -> "LndTools":
        return cls(lnd_node=lnd_node)

    def _decode_invoice_tool(self):
        @tool
        def decode_invoice(invoice: str) -> ln.PayReq:
            """
            Takes an encoded payment request (also called an invoice) string
            and attempts to decode it, returning a full description of the
            conditions encoded within the payment request.

            An example invoice in a JSON-like format looks like:
            {
                destination: <string>,
                payment_hash: <string>,
                num_satoshis: <int64>,
                timestamp: <int64>,
                expiry: <int64>,
                description: <string>,
                description_hash: <string>,
                fallback_addr: <string>,
                cltv_expiry: <int64>,
                route_hints: <RouteHint>,
                payment_addr: <bytes>,
                num_msat: <int64>,
                features: <FeaturesEntry>,
            }

            This can be used to get more information about an invoice before
            trying to pay it.
            """
            decoded_invoice = self.lnd_node.decode_invoice(invoice)
            return decoded_invoice

        return decode_invoice

    def _send_payment_tool(self):
        @tool
        def send_payment(invoice: str) -> ln.SendResponse:
            """
            Can be used to make a payment to a valid Lightning invoice.
            Information about the payment is returned, such as the pre-image,
            the route it took, the amount of fees paid.

            An example of a JSON-like response is:
            {
                payment_error: <string>,
                payment_preimage: <bytes>,
                payment_route: <Route>,
                payment_hash: <bytes>,
            }
            """
            payment_resp = self.lnd_node.send_payment(invoice)
            return payment_resp

        return send_payment

    def _channel_balance_tool(self):
        @tool
        def channel_balance() -> ln.ChannelBalanceResponse:
            """
            Returns the current off-chain balance of a node. This is the amount
            of satoshis channels, or the total amount the node has on the
            Lightning Network.

            An example of a JSON-like response is:

            {
                balance: <int64>,
                pending_open_balance: <int64>,
                local_balance: <Amount>,
                remote_balance: <Amount>,
                unsettled_local_balance: <Amount>,
                unsettled_remote_balance: <Amount>,
                pending_open_local_balance: <Amount>,
                pending_open_remote_balance: <Amount>,
            }

            """
            return self.lnd_node.channel_balance()

        return channel_balance

    def _wallet_balance_tool(self):
        @tool
        def wallet_balance() -> ln.WalletBalanceResponse:
            """
            Returns the current on-chain balance of a node. This is the amount
            of satoshis that a node has in non-channel UTXOs (unspent
            transaction outputs).

            An example JSON-like response is:

            {
                total_balance: <int64>,
                confirmed_balance: <int64>,
                unconfirmed_balance: <int64>,
                locked_balance: <int64>,
                reserved_balance_anchor_chan: <int64>,
                account_balance: <AccountBalanceEntry>,
            }
            """
            return self.lnd_node.wallet_balance()

        return wallet_balance

    def _get_info_tool(self):
        @tool
        def get_info() -> ln.GetInfoResponse:
            """
            Returns general information about an lnd node. This includes things
            like how many channels a node has, its public key, current height.

            An example of a JSON-like response is:

            {
                "version": <string>,
                "commit_hash": <string>,
                "identity_pubkey": <string>,
                "alias": <string>,
                "num_pending_channels": <uint32>,
                "num_active_channels": <uint32>,
                "num_inactive_channels": <uint32>,
                "num_peers": <uint32>,
                "block_height": <uint32>,
                "block_hash": <string>,
                "best_header_timestamp": <int64>,
                "synced_to_chain": <bool>,
                "synced_to_graph": <bool>,
                "testnet": <bool>,
                "chains": <Chain>,
                "uris": <string>,
                "features": <FeaturesEntry>,
            }
            """
            return self.lnd_node.get_info()

        return get_info

    def _check_invoice_status(self):
        pass

    def _create_invoice(self):
        @tool
        def create_invoice(memo: str, value: int) -> ln.AddInvoiceResponse:
            """
            Creates a new invoice on the Lightning Network. This in invoice can
            be used to receiveds funds on Lightning.

            An example of a JSON-like response is:
             {
                r_hash: <bytes>,
                payment_request: <string>,
                add_index: <uint64>,
                payment_addr: <bytes>,
            }

            """
            return self.lnd_node.create_invoice(memo, value)

        return create_invoice

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""

        tools = []

        for attribute_name in dir(self):
            if attribute_name.endswith('_tool'):
                attribute = getattr(self, attribute_name)

                if attribute is None:
                    continue

                tool_func = attribute()

                if tool_func is None:
                    continue

                if callable(attribute):
                    tools.append(attribute())

        return tools
