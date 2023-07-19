import pickle
import sys
from multiprocessing import Process
from miner import Block

def read():
  with open("./testfile", 'rb') as file:
    blockchain = pickle.load(file)
    for block in blockchain[-10:]:
      print(block.index)
      print(block.timestamp)
      print(block.data)
      print(block.hash)
      print(block.previous_hash)
      print("===========")
    # print(str(round(sys.getsizeof(blockchain) / 1024 / 1024, 3)) + "MB")
    print(sys.getsizeof(blockchain))
    
    with open("./testfile", 'wb') as file:
      pickle.dump(blockchain, file)


if __name__ == "__main__":
  read()

  # 1080088
  # 17293215