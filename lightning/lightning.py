from protos import lightning_pb2 as ln
from protos import lightning_pb2_grpc as lnrpc

import grpc
import os

import codecs

import binascii

# Due to updated ECDSA generated tls.cert we need to let gprc know that we need
# to use that cipher suite otherwise there will be a handhsake error when we
# communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

class LightningNode(object):
    """
    """

    def pay_invoice(self, invoice):
        raise NotImplementedError()

class LndNode(LightningNode):
    """
    """

    def __init__(self, cert_path, macaroon_path, host='localhost', port='10009'):
        self.cert_path = cert_path
        self.macaroon_path = macaroon_path
        self.host = host
        self.port = port

        # TODO(roasbeef): pick out other details for cert + macaroon path

        self._grpc_conn = None

        with open(os.path.expanduser(self.cert_path), 'rb') as f:
            cert_bytes = f.read()
            self._cert_creds = grpc.ssl_channel_credentials(cert_bytes)

        with open(os.path.expanduser(self.macaroon_path), 'rb') as f:
            macaroon_bytes = f.read()
            self._macaroon = codecs.encode(macaroon_bytes, 'hex')

        def metadata_callback(context, callback):
            # for more info see grpc docs
            callback([('macaroon', self._macaroon)], None)

        # now build meta data credentials
        auth_creds = grpc.metadata_call_credentials(metadata_callback)

        # combine the cert credentials and the macaroon auth credentials
        # such that every call is properly encrypted and authenticated
        combined_creds = grpc.composite_channel_credentials(
                self._cert_creds, auth_creds,
        )

        # finally pass in the combined credentials when creating a channel
        channel = grpc.secure_channel(
                '{}:{}'.format(host, port), combined_creds,
        )

        self._grpc_conn = lnrpc.LightningStub(channel)

    def pay_invoice(self, invoice, amt=None):
        pay_resp = self._grpc_conn.SendPaymentSync(
                ln.SendRequest(payment_request=invoice, amt=amt),
        )

        pre_image = binascii.hexlify(pay_resp.payment_preimage).decode('utf-8')

        return pre_image

    def send_payment(self, invoice):
        return self._grpc_conn.SendPaymentSync(
                ln.SendRequest(payment_request=invoice),
        )

    def decode_invoice(self, invoice):
        req = ln.PayReqString(pay_req=invoice)
        decode_resp = self._grpc_conn.DecodePayReq(req)

        return decode_resp

    def channel_balance(self):
        return self._grpc_conn.ChannelBalance(ln.ChannelBalanceRequest())

    def wallet_balance(self):
        return self._grpc_conn.WalletBalance(ln.WalletBalanceRequest())

    def get_info(self):
        return self._grpc_conn.GetInfo(ln.GetInfoRequest())
