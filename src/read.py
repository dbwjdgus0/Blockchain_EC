import pickle
import sys
from multiprocessing import Process
from miner import Block

def read():
  with open("./test_file2023-07-13 04:14:11.904891", 'rb') as file:
    blockchain = pickle.load(file)
    for block in blockchain:
      print(block.index)
      print(block.timestamp)
      print(block.data)
      print(block.hash)
      print(block.previous_hash)
      print("===========")
    print(str(round(sys.getsizeof(blockchain) / 1024 / 1024, 3)) + "MB")
      

if __name__ == "__main__":
  process = Process(target=read)
  process.start()
  process.join()