import requests
import time
import base64
import ecdsa

addr_from = "gYKa1OqrP4op2+zIm+YI64Fwn9d8hn03nXClOh3a4H8FtD+dpTT9k/xPfVDrj/Ux275aWveuozdA44JQmzdnHQ=="
private_key = "5b3b2d6abee547adbd490f099f3f4414f16a138cab4f4937e19f44adad6d42ff"
addr_to = "0le3DBDMglT+JNHQ+dFBHoFlE813bp4EOxumSI0O01vi02wOWT3d5Z9nUycTV1fi9h7yzwLgEX9DSHpT6W9hsw=="
amount = "3000"

def infinite_transactions():
  t1 = time.time()
  cnt = 0
  while True:
    cnt += 1
    send_transaction(addr_from, private_key, addr_to, amount)
    if(cnt % 500 == 0):
        t2 = time.time()
        print("{} transaction sent".format(cnt))
        print("{} sec over".format(t2 - t1))

def send_transaction(addr_from, private_key, addr_to, amount):
    if len(private_key) == 64:
        signature, message = sign_ECDSA_msg(private_key)
        url = 'http://localhost:5000/txion'
        payload = {"from": addr_from,
                   "to": addr_to,
                   "amount": amount,
                   "signature": signature.decode(),
                   "message": message}
        headers = {"Content-Type": "application/json"}

        res = requests.post(url, json=payload, headers=headers)
        # print(res.text)
    else:
        print("Wrong address or key length! Verify and try again.")

def sign_ECDSA_msg(private_key):
    """Sign the message to be sent
    private_key: must be hex

    return
    signature: base64 (to make it shorter)
    message: str
    """
    # Get timestamp, round it, make it into a string and encode it to bytes
    message = str(round(time.time()))
    bmessage = message.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(bmessage))
    return signature, message


if __name__ == '__main__':
    infinite_transactions()