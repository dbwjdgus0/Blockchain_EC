import time
import hashlib
import json
import requests
import base64
from flask import Flask, request
from multiprocessing import Process, Pipe, Queue
import ecdsa
import sys
from datetime import datetime 
import pickle

from miner_config import MINER_ADDRESS, MINER_NODE_URL, PEER_NODES

from pyeclib.ec_iface import ECDriver

node = Flask(__name__)

# BLOCK_SIZE = 67108864 #64MB
# BLOCK_SIZE = 33554432 #32MB
BLOCK_SIZE = 1048576 #1MB
# BLOCK_SIZE = 65536 #64KB

def write_block(blockchain, t1):
    path_base = "./block_result"
    file_name = "res_" + datetime.now().strftime("%Y_%m_%d_%H:%M:%S")
    print("blockchain size: {}".format(sys.getsizeof(blockchain)))
    with open("%s/%s" % (path_base, file_name) , 'wb') as file:
        pickle.dump(blockchain, file)
        # for block in blockchain:
        #     temp = {}
        #     temp['index'] = block['index']
        #     temp['timestamp'] = block['timestamp']
        #     temp['data'] = str(block['data'])
        #     temp['previous_hash'] = block['previous_hash']
        #     temp['hash'] = block['hash']
        #     file.write(str(temp))
    t2 = time.time()
    print("Block write - file name: {}, block size: {} MB, time: {} sec".format(file_name, BLOCK_SIZE / 1024 / 1024, t2-t1))
    encode_block(path_base, file_name)


def encode_block(path_base, file_name, k = 2, m = 4, ec_type = "liberasurecode_rs_vand", fragment_dir = "./encoded"):
    t1 = time.time()

    ec_driver = ECDriver(k=k, m=m, ec_type=ec_type)
    # read
    with open("%s/%s" % (path_base, file_name), "rb") as fp:
        whole_file_str = fp.read()

    # encode
    print("EC input size: {}".format(sys.getsizeof(whole_file_str)))
    fragments = ec_driver.encode(whole_file_str)
    # store
    i = 0
    for fragment in fragments:
        with open("%s/%s.%d" % (fragment_dir, file_name, i), "wb") as fp:
            fp.write(fragment)
        i += 1
    t2 = time.time()
    print("Encoded - file name: {}, block size: {} MB, time: {} sec, k: {}, p: {}, ec_type: {}".format(file_name, BLOCK_SIZE / 1024 / 1024, t2-t1, k, m, ec_type))



def block_to_json(blockchain):
    path_base = "./json_block/"
    for block in blockchain:
        file_path = path_base + str(datetime.now())
        json_block = {
            "index": str(block.index),
            "timestamp": str(block.timestamp),
            "data": block.data,
            "hash": block.hash,
            "previous_hash": block.previous_hash
        }
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(json_block, file)


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        """Returns a new Block object. Each block is "chained" to its previous
        by calling its unique hash.

        Args:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.

        Attrib:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.
            hash(str): Current block unique hash.

        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def hash_block(self):
        """Creates the unique hash for the block. It uses sha256."""
        sha = hashlib.sha256()
        sha.update((str(self.index) + str(self.timestamp) + str(self.data) + str(self.previous_hash)).encode('utf-8'))
        return sha.hexdigest()


def gen_block(idx, timestamp, data, prev_hash):
    new_block = {
        'index': idx,
        'timestamp': timestamp,
        'data': data,
        'previous_hash': prev_hash,
    }
    new_hash = hash_block(new_block)
    new_block['hash'] = new_hash

    return new_block
    
def hash_block(new_block):
    """Creates the unique hash for the block. It uses sha256."""
    sha = hashlib.sha256()
    sha.update((str(new_block['index']) + str(new_block['timestamp']) + str(new_block['data']) + str(new_block['previous_hash'])).encode('utf-8'))
    return sha.hexdigest()


def create_genesis_block():
    """To create each block, it needs the hash of the previous one. First
    block has no previous, so it must be created manually (with index zero
     and arbitrary previous hash)"""
    return Block(0, time.time(), {
        "proof-of-work": 9,
        "transactions": None},
        "0")

# def create_genesis_block():
#     """To create each block, it needs the hash of the previous one. First
#     block has no previous, so it must be created manually (with index zero
#      and arbitrary previous hash)"""
#     return gen_block(0, time.time(), { "proof-of-work": 9, "transactions": None}, "0")


# Node's blockchain copy
BLOCKCHAIN = [create_genesis_block()]

""" Stores the transactions that this node has in a list.
If the node you sent the transaction adds a block
it will get accepted, but there is a chance it gets
discarded and your transaction goes back as if it was never
processed"""
NODE_PENDING_TRANSACTIONS = []


def proof_of_work(last_proof, blockchain):
    # Creates a variable that we will use to find our next proof of work
    incrementer = last_proof + 1
    # Keep incrementing the incrementer until it's equal to a number divisible by 7919
    # and the proof of work of the previous block in the chain
    start_time = time.time()
    # while not (incrementer % 7919 == 0 and incrementer % last_proof == 0):
    incrementer += 1
    # Check if any node found the solution every 60 seconds
        # if int((time.time()-start_time) % 60) == 0:
            # If any other node got the proof, stop searching
    new_blockchain = consensus(blockchain)
    if new_blockchain:
        # (False: another node got proof first, new blockchain)
        return False, new_blockchain
    # Once that number is found, we can return it as a proof of our work
    return incrementer, blockchain


def mine(queue, blockchain, node_pending_transactions):
    BLOCKCHAIN = blockchain
    NODE_PENDING_TRANSACTIONS = node_pending_transactions
    loop_cnt = 0
    t1 = time.time()
    while True:

        """Mining is the only way that new coins can be created.
        In order to prevent too many coins to be created, the process
        is slowed down by a proof of work algorithm.
        """
        # Get the last proof of work
        
        
        last_block = BLOCKCHAIN[-1]
        last_proof = last_block.data['proof-of-work']
        # last_proof = last_block['data']['proof-of-work']
        
        
        # Find the proof of work for the current block being mined
        # Note: The program will hang here until a new proof of work is found
        
        proof = proof_of_work(last_proof, BLOCKCHAIN)
        
        # If we didn't guess the proof, start mining again
        
        if not proof[0]:
            # Update blockchain and save it to file
            BLOCKCHAIN = proof[1]
            # a.send(BLOCKCHAIN)
            continue
        else:
            # Once we find a valid proof of work, we know we can mine a block so
            # ...we reward the miner by adding a transaction
            # First we load all pending transactions sent to the node server
            
            # 찾았다
            # NODE_PENDING_TRANSACTIONS = requests.get(url = MINER_NODE_URL + '/txion', params = {'update':MINER_ADDRESS}).content
            # NODE_PENDING_TRANSACTIONS = json.loads(NODE_PENDING_TRANSACTIONS)
            
            if queue.empty():
                NODE_PENDING_TRANSACTIONS = []
            else:
                NODE_PENDING_TRANSACTIONS = queue.get()

            # Then we add the mining reward
            NODE_PENDING_TRANSACTIONS.append({
                "from": "network",
                "to": MINER_ADDRESS,
                "amount": 1})
            # Now we can gather the data needed to create the new block
            new_block_data = {
                "proof-of-work": proof[0],
                "transactions": list(NODE_PENDING_TRANSACTIONS)
            }
            new_block_index = last_block.index + 1
            new_block_timestamp = time.time()
            last_block_hash = last_block.hash
            # Empty transaction list
            NODE_PENDING_TRANSACTIONS = []
            # Now create the new block
            mined_block = Block(new_block_index, new_block_timestamp, new_block_data, last_block_hash)

            # mined_block = gen_block(new_block_index, new_block_timestamp, new_block_data, last_block_hash)
            BLOCKCHAIN.append(mined_block)
            # Let the client know this node mined a block

            # a.send(BLOCKCHAIN)
            # requests.get(url = MINER_NODE_URL + '/blocks', params = {'update':MINER_ADDRESS})
        
        if(sys.getsizeof(BLOCKCHAIN) > BLOCK_SIZE):
            write_block(BLOCKCHAIN, t1)
            BLOCKCHAIN = [create_genesis_block()]
            print("SAVED!!")
            t1 = time.time()
            break
        else:
            if loop_cnt % 50 == 0:
                print(str(round(sys.getsizeof(BLOCKCHAIN) / 1024, 3)) + " KB")
                print(str(round(sys.getsizeof(BLOCKCHAIN) / BLOCK_SIZE * 100 , 3)) + "%" +" done")



def find_new_chains():
    # Get the blockchains of every other node
    other_chains = []
    for node_url in PEER_NODES:
        # Get their chains using a GET request
        block = requests.get(url = node_url + "/blocks").content
        # Convert the JSON object to a Python dictionary
        block = json.loads(block)
        # Verify other node block is correct
        validated = validate_blockchain(block)
        if validated:
            # Add it to our list
            other_chains.append(block)
    return other_chains


def consensus(blockchain):
    # Get the blocks from other nodes
    other_chains = find_new_chains()
    # If our chain isn't longest, then we store the longest chain
    BLOCKCHAIN = blockchain
    longest_chain = BLOCKCHAIN
    for chain in other_chains:
        if len(longest_chain) < len(chain):
            longest_chain = chain
    # If the longest chain wasn't ours, then we set our chain to the longest
    if longest_chain == BLOCKCHAIN:
        # Keep searching for proof
        return False
    else:
        # Give up searching proof, update chain and start over again
        BLOCKCHAIN = longest_chain
        return BLOCKCHAIN


def validate_blockchain(block):
    """Validate the submitted chain. If hashes are not correct, return false
    block(str): json
    """
    return True


@node.route('/blocks', methods=['GET'])
def get_blocks():
    # Load current blockchain. Only you should update your blockchain
    if request.args.get("update") == MINER_ADDRESS:
        global BLOCKCHAIN
        # BLOCKCHAIN = pipe_input.recv()
    chain_to_send = BLOCKCHAIN
    # Converts our blocks into dictionaries so we can send them as json objects later
    chain_to_send_json = []
    for block in chain_to_send:
        block = {
            "index": str(block.index),
            "timestamp": str(block.timestamp),
            "data": str(block.data),
            "hash": block.hash
        }
        chain_to_send_json.append(block)

    # Send our chain to whomever requested it
    chain_to_send = json.dumps(chain_to_send_json, sort_keys=True)
    return chain_to_send


@node.route('/txion', methods=['GET', 'POST'])
def transaction():
    """Each transaction sent to this node gets validated and submitted.
    Then it waits to be added to the blockchain. Transactions only move
    coins, they don't create it.
    """
    if request.method == 'POST':
        # On each new POST request, we extract the transaction data
        new_txion = request.get_json()
        # Then we add the transaction to our list
        if validate_signature(new_txion['from'], new_txion['signature'], new_txion['message']):
            NODE_PENDING_TRANSACTIONS.append(new_txion)
            # Because the transaction was successfully
            # submitted, we log it to our console

            # print("New transaction")
            # print("FROM: {0}".format(new_txion['from']))
            # print("TO: {0}".format(new_txion['to']))
            # print("AMOUNT: {0}\n".format(new_txion['amount']))

            # Then we let the client know it worked out
            queue.put(NODE_PENDING_TRANSACTIONS)
            return "Transaction submission successful\n"
        else:
            return "Transaction submission failed. Wrong signature\n"
    # Send pending transactions to the mining process
    elif request.method == 'GET' and request.args.get("update") == MINER_ADDRESS:
        pending = json.dumps(NODE_PENDING_TRANSACTIONS, sort_keys=True)
        # Empty transaction list
        NODE_PENDING_TRANSACTIONS[:] = []
        return pending


def validate_signature(public_key, signature, message):
    """Verifies if the signature is correct. This is used to prove
    it's you (and not someone else) trying to do a transaction with your
    address. Called when a user tries to submit a new transaction.
    """
    public_key = (base64.b64decode(public_key)).hex()
    signature = base64.b64decode(signature)
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
    # Try changing into an if/else statement as except is too broad.
    try:
        return vk.verify(signature, message.encode())
    except:
        return False


def welcome_msg():
    print("""       =========================================\n
        SIMPLE COIN v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n
        You can find more help at: https://github.com/cosme12/SimpleCoin\n
        Make sure you are using the latest version or you may end in
        a parallel chain.\n\n\n""")


if __name__ == '__main__':
    welcome_msg()

    queue = Queue()

    pipe_output, pipe_input = Pipe()
    miner_process = Process(target=mine, args=(queue, BLOCKCHAIN, NODE_PENDING_TRANSACTIONS))
    miner_process.start()
   
    transactions_process = Process(target=node.run(), args=(queue, ))
    transactions_process.start()

    miner_process.join()
    transactions_process.join()

