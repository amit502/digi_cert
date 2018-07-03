"""
Connectors supporting Bitcoin transaction lookups. This is used in the Blockchain Certificates project
(http://www.blockcerts.org/) for validating certificates on the blockchain.
"""
import logging
import sys
import requests
from cert_core import BlockchainType, BlockcertVersion, Chain
from cert_core import PUBKEY_PREFIX
import json
from . import IssuerInfo, IssuerKey
from . import TransactionData
from .errors import *
from Naked.toolshed.shell import execute_js, muterun_js
from . import issuer_contract
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


def createTransactionLookupConnector(chain=Chain.bitcoin_mainnet, options=None):
    """
    :param chain: which chain, supported values are testnet and mainnet
    :return: connector for looking up transactions
    """
    if chain == Chain.mockchain or chain == Chain.bitcoin_regtest:
        return MockConnector(chain)
    elif chain.blockchain_type == BlockchainType.ethereum:
        if options and 'etherscan_api_token' in options:
            etherscan_api_token = options['etherscan_api_token']
        else:
            etherscan_api_token = None
        return EtherscanConnector(chain, etherscan_api_token)
    return FallbackConnector(chain)


class TransactionLookupConnector:
    """
    Abstract connector for looking up transactions
    """

    def __init__(self):
        self.url = None

    def lookup_tx(self, txid):
        json_response = self.fetch_tx(txid)
        return self.parse_tx(json_response)

    def fetch_tx(self, txid):
        print(self.url % txid)
        r = requests.get(self.url % txid, headers=headers)
        if r.status_code != 200:
            logging.error('Error looking up transaction_id with url=%s, status_code=%d', self.url % txid, r.status_code)
            raise InvalidTransactionError('error looking up transaction_id=%s' % txid)
        return r.json()

    def parse_tx(self, json_response):
        """
        Abstract method for parsing json response
        :param json_response: json returned by transaction connector
        :return: TransactionData
        """
        return None


class MockConnector(TransactionLookupConnector):
    def __init__(self, chain):
        self.chain = chain

    def lookup_tx(self, txid):
        return True

class FallbackConnector(TransactionLookupConnector):
    def __init__(self, chain):
        self.chain = chain
        self.connectors = [BlockcypherConnector(chain), BlockrIOConnector(chain)]

    def lookup_tx(self, txid):
        exceptions = []
        for connector in self.connectors:
            try:
                response = connector.lookup_tx(txid)
                if response:
                    return response
            except Exception as e:
                logging.warning('Error looking up transaction, trying more connectors')
                exceptions.append(e)
        raise InvalidTransactionError(exceptions)


class BlockchainInfoConnector(TransactionLookupConnector):
    """
    Lookup blockchain transactions using blockchain.info api. Currently only the 'mainnet' chain is supported in this
    connector.
    """

    def __init__(self, chain=Chain.bitcoin_mainnet):
        if chain != Chain.bitcoin_mainnet:
            raise Exception('only mainnet chain is supported with blockchain.info collector')
        self.url = 'https://blockchain.info/rawtx/%s?cors=true'

    def parse_tx(self, json_response):
        revoked = set()
        script = None
        signing_key = json_response['inputs'][0]['prev_out']['addr']
        for o in json_response['out']:
            if int(o.get('value', 1)) == 0:
                script = o['script'][4:]
            else:
                if o.get('spent'):
                    revoked.add(o.get('addr'))
        if not script:
            logging.error('transaction response is missing op_return script: %s', json_response)
            raise InvalidTransactionError('transaction response is missing op_return script' % json_response)
        return TransactionData(signing_key, script, None, revoked)


class BlockrIOConnector(TransactionLookupConnector):
    def __init__(self, chain):
        if chain == Chain.bitcoin_testnet:
            self.url = 'https://tbtc.blockr.io/api/v1/tx/info/%s'
        elif chain == Chain.bitcoin_mainnet:
            self.url = 'https://btc.blockr.io/api/v1/tx/info/%s'
        else:
            raise Exception(
                'unsupported chain (%s) requested with BlockrIO collector. Currently only testnet and mainnet are supported' % chain)

    def parse_tx(self, json_response):
        revoked = set()
        script = None
        time = json_response['data']['time_utc']
        signing_key = json_response['data']['vins'][0]['address']
        for o in json_response['data']['vouts']:
            if float(o.get('amount', 1)) == 0:
                if not 'extras' in o:
                    script = None
                else:
                    script = o['extras']['script'][4:]
            else:
                if o.get('is_spent') and float(o.get('is_spent', 1)) == 49:
                    revoked.add(o.get('address'))
        if not script:
            logging.error('transaction response is missing op_return script: %s', json_response)
            raise InvalidTransactionError('transaction response is missing op_return script')
        return TransactionData(signing_key, script, time, revoked)


class BlockcypherConnector(TransactionLookupConnector):
    """
    Lookup blockchain transactions using blockcypher api. Currently the 'mainnet' and 'testnet' chains are supported in
    this connector.
    """

    def __init__(self, chain):
        if chain == Chain.bitcoin_testnet:
            self.url = 'http://api.blockcypher.com/v1/btc/test3/txs/%s?limit=100'
        elif chain == Chain.bitcoin_mainnet:
            self.url = 'https://api.blockcypher.com/v1/btc/main/txs/%s?limit=100'
        else:
            raise Exception(
                'unsupported chain (%s) requested with blockcypher collector. Currently only testnet and mainnet are supported' % chain)

    def parse_tx(self, json_response):
        revoked = set()
        script = None
        time = json_response['received']
        signing_key = json_response['inputs'][0]['addresses'][0]
        for o in json_response['outputs']:
            if float(o.get('value', 1)) == 0:
                script = o['data_hex']
            else:
                if o.get('spent_by'):
                    revoked.add(o.get('addresses')[0])
        if not script:
            logging.error('transaction response is missing op_return script: %s', json_response)
            raise InvalidTransactionError('transaction response is missing op_return script' % json_response)
        return TransactionData(signing_key, script, time, revoked)


def get_remote_json(the_url):
    r = requests.get(the_url, timeout=10) # timeout is in seconds
    if r.status_code != 200:
        logging.error('Error looking up url=%s, status_code=%d', the_url, r.status_code)
        return None
    else:
        remote_json = r.json()
        logging.debug('Found results at url=%s', the_url)
        return remote_json


class EtherscanConnector(TransactionLookupConnector):

    def __init__(self, chain, api_key):
        if chain == Chain.ethereum_mainnet:
            url_prefix = 'https://api.etherscan.io'
        elif chain == Chain.ethereum_ropsten:
            url_prefix = 'https://ropsten.etherscan.io'
        else:
            raise Exception(
                'unsupported chain (%s) requested with Etherscan collector. Currently only mainnet and ropsten are supported' % chain)

        self.url = url_prefix + '/api?module=proxy&action=eth_getTransactionByHash&apikey=' + 'WY2IpmvumcQOxVcCxUW4' + '&txhash=%s'
        print(self.url)
        self.timestamp_url = url_prefix + '/api?module=block&action=getblockreward&apikey=' + 'WY2IpmvumcQOxVcCxUW4' + '&blockno=%s'

    def parse_tx(self, json_response):
        # https://api.etherscan.io/
        print(self.timestamp_url)
        signing_key = json_response['result']['from']
        script = json_response['result']['input']
        block_no = json_response['result']['blockNumber']
        if not script:
            logging.error('transaction response is missing input: %s', json_response)
            raise InvalidTransactionError('transaction response is missing input')
        if not block_no:
            logging.error('transaction is not yet confirmed: %s', json_response)
            raise InvalidTransactionError('transaction is not yet confirmed')
        ts_url = self.timestamp_url % str(int(block_no, 16))
        print(ts_url)
        r = requests.get(ts_url, headers=headers)
        print(r.json())
        if r.status_code != 200:
            logging.error('Error looking up block timestamp with url=%s, status_code=%d', ts_url, r.status_code)
            raise InvalidTransactionError('error looking up block timestamp=%s' % block_no)
        date_time = r.json()['result']['timeStamp']
        return TransactionData(signing_key, script, date_time_utc=int(date_time), revoked_addresses=None)


def get_field_or_default(data, field_name):
    if field_name in data:
        return data[field_name]
    else:
        return None


def get_issuer_info(certificate_model):
    #issuer_json = get_remote_json(certificate_model.issuer.id)
    ipfs_hash_from_contract=issuer_contract.get_hash();
    if certificate_model.issuer.id!=ipfs_hash_from_contract:
        print("hey")
        sys.exit("The ipfs hash of the issuer is  not valid!!!!");
    response = muterun_js('E:/Git/cert-viewer/cert_viewer/static/js/file.js',ipfs_hash_from_contract)
    if response.exitcode == 0:
      issuer_json=response.stdout
      issuer_json=issuer_json.decode("utf-8") 
      issuer_json=json.loads(issuer_json)
      #logging.debug(issuer_json)     
    else:
      sys.stderr.write(response.stderr.decode("utf-8"))
    
    if not issuer_json:
        raise Exception('Issuer URL returned no results ' + certificate_model.issuer.id)

    # we use the revocation list in the certificate
    revoked_assertions = []
    v2ish = certificate_model.version == BlockcertVersion.V2 or certificate_model.version == BlockcertVersion.V2_ALPHA
    if v2ish:
        if 'revocationList' in certificate_model.certificate_json['badge']['issuer']:
            revocation_url = certificate_model.certificate_json['badge']['issuer']['revocationList']
            revoked_json = get_remote_json(revocation_url)
            if revoked_json and revoked_json['revokedAssertions']:
                revoked_assertions = [r['id'] for r in revoked_json['revokedAssertions']]

    issuer_keys = []

    if '@context' in issuer_json:
        if 'publicKey' in issuer_json:
            for public_key in issuer_json['publicKey']:
                pk = public_key['id'][len(PUBKEY_PREFIX):]
                created = get_field_or_default(public_key, 'created')
                expires = get_field_or_default(public_key, 'expires')
                revoked = get_field_or_default(public_key, 'revoked')
                issuer_keys.append(IssuerKey(pk, created, expires, revoked))
        # Backcompat for v2 alpha issuer
        elif 'publicKeys' in issuer_json:
            for public_key in issuer_json['publicKeys']:
                pk = public_key['publicKey'][len(PUBKEY_PREFIX):]

                created = get_field_or_default(public_key, 'created')
                expires = get_field_or_default(public_key, 'expires')
                revoked = get_field_or_default(public_key, 'revoked')
                issuer_keys.append(IssuerKey(pk, created, expires, revoked))
        return IssuerInfo(issuer_keys, revoked_assertions=revoked_assertions)
    else:
        # V1 issuer format
        issuer_key = IssuerKey(issuer_json['issuerKeys'][0]['key'])
        if revoked_assertions:
            # this is a v2 certificate with legacy issuer format
            return IssuerInfo([issuer_key], revoked_assertions=revoked_assertions)
        else:
            revocation_key = IssuerKey(issuer_json['revocationKeys'][0]['key'])
            issuer_info = IssuerInfo([issuer_key], revocation_keys=[revocation_key])
            return issuer_info
