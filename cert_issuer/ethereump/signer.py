import rlp
from ethereum import transactions
from ethereum.utils import encode_hex

from errors import UnableToSignTxError
from models import Signer

import logging
import os
import time

import requests

from models import SecretManager

class EthereumSigner(Signer):
    def __init__(self, ethereum_chain):
        self.ethereum_chain = ethereum_chain
        # Netcode ensures replay protection (see EIP155)
        if ethereum_chain.external_display_value == 'ethereumMainnet':
            self.netcode = 1
        elif ethereum_chain.external_display_value == 'ethereumRopsten':
            self.netcode = 3
        else:
            self.netcode = None

    # wif = unencrypted private key as string in the first line of the supplied private key file
    def sign_message(self, wif, message_to_sign):
        pass

    def sign_transaction(self, wif, transaction_to_sign):
        ##try to sign the transaction.

        if isinstance(transaction_to_sign, transactions.Transaction):
            try:
                raw_tx = rlp.encode(transaction_to_sign.sign(wif, self.netcode))
                raw_tx_hex = encode_hex(raw_tx)
                return raw_tx_hex
            except Exception as msg:
                return {'error': True, 'message': msg}
        else:
            raise UnableToSignTxError('You are trying to sign a non transaction type')
			
			
class FileSecretManager(SecretManager):
    def __init__(self, signer, path_to_secret, safe_mode=True, issuing_address=None):
        super().__init__(signer)
        self.path_to_secret = path_to_secret
        self.safe_mode = safe_mode
        self.issuing_address = issuing_address

    def start(self):
        if self.safe_mode:
            check_internet_off(self.path_to_secret)
        else:
            logging.warning(
                'app is configured to skip the wifi check when the USB is plugged in. Read the documentation to'
                ' ensure this is what you want, since this is less secure')

        self.wif = import_key(self.path_to_secret)

    def stop(self):
        self.wif = None
        if self.safe_mode:
            check_internet_on(self.path_to_secret)
        else:
            logging.warning(
                'app is configured to skip the wifi check when the USB is plugged in. Read the documentation to'
                ' ensure this is what you want, since this is less secure')


class FinalizableSigner(object):
    def __init__(self, secret_manager):
        self.secret_manager = secret_manager

    def __enter__(self):
        logging.info('Starting finalizable signer')
        self.secret_manager.start()
        return self.secret_manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info('Stopping finalizable signer')
        self.secret_manager.stop()


def import_key(secrets_file_path):
    with open(secrets_file_path) as key_file:
        key = key_file.read().strip()
    return key


def internet_on():
    """Pings Google to see if the internet is on. If online, returns true. If offline, returns false."""
    try:
        requests.get('http://google.com')
        return True
    except requests.exceptions.RequestException:
        return False


def check_internet_off(secrets_file_path):
    """If internet off and USB plugged in, returns true. Else, continues to wait...""" #internet_on() is False and 
    while True:
        if os.path.exists(secrets_file_path):
            break
        else:
            print("Turn off your internet and plug in your USB to continue...",secrets_file_path)
            time.sleep(10)
    return True


def check_internet_on(secrets_file_path):
    """If internet on and USB unplugged, returns true. Else, continues to wait..."""
    while True:
        if internet_on() is True and not os.path.exists(secrets_file_path):
            break
        else:
            print("Turn on your internet and unplug your USB to continue...")
            time.sleep(10)
    return True

