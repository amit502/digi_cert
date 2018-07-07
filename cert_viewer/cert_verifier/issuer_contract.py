import time
from web3 import Web3, HTTPProvider
import json
import os

w3 = Web3(HTTPProvider('https://ropsten.infura.io/WY2IpmvumcQOxVcCxUW4'))
contract_address     = w3.toChecksumAddress('0x6adfdc4f2a3cffaaa3106d0a197cda8ea7723e8b')
wallet_private_key   = '5077f71a0dda695f8c1f1ea9b8f69e0800541f23b1f61e0cb67148e715167901'
wallet_address       = w3.toChecksumAddress('0x37f5257621fe96835bbb49e453e3db37428b8a55')



w3.eth.enable_unaudited_features()
path=os.path.join(os.getcwd(),'cert_viewer/cert_verifier/mycontract.json')
with open(path) as f:
    info_json = json.load(f)
abi = info_json["abi"]
contract=w3.eth.contract(address=contract_address,abi=abi)


def get(value):

    nonce = w3.eth.getTransactionCount(wallet_address)

    txn_dict = contract.functions.get(value).call()

    
    return txn_dict

def set(value):
    nonce = w3.eth.getTransactionCount(wallet_address)

    txn_dict = contract.functions.set(value).buildTransaction({
        'chainId': 3,
        'gas': 140000,
        'gasPrice': w3.toWei('40', 'gwei'),
        'nonce': nonce,
    })

    signed_txn = w3.eth.account.signTransaction(txn_dict, private_key=wallet_private_key)

    result = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    tx_receipt = w3.eth.getTransactionReceipt(result)

    count = 0
    while tx_receipt is None and (count < 30):

        time.sleep(10)

        tx_receipt = w3.eth.getTransactionReceipt(result)

        print(tx_receipt)


    if tx_receipt is None:
        return {'status': 'failed', 'error': 'timeout'}

    
    return tx_receipt

#print(set("zb2rhnXSBvFwDDPwcfyRMrBbGArkpmTJ4yBjZShcbrAcT5wHX"))
#print(get("zb2rhnXSBvFwDDPwcfyRMrBbGArkpmTJ4yBjZShcbrAcT5wHX"))

    


