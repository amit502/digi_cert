from Naked.toolshed.shell import execute_js, muterun_js
import json
import sha3
import re
import sys

response = muterun_js('../static/js/file.js',"zb2rhnXSBvFwDDPwcfyRMrBbGArkpmTJ4yBjZShcbrAcT5wHX")
if response.exitcode == 0:
  issuer_json=response.stdout
  print(response.stdout)
  issuer_json=issuer_json.decode('utf-8')
  
  issuer_json=json.loads(issuer_json)
  #print(issuer_json)     
else:
  sys.stderr.write(response.stderr.decode("UTF-8"))

a={"0x37f5257621fE96835BbB49E453E3dB37428b8A55":"0x37f5257621fE96835BbB49E453E3dB37428b8A55"}
b="0x37f5257621fe96835bbb49e453e3db37428b8a55"
if b in a:
  print("OK")



