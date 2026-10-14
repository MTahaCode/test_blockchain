import hashlib, time

class Block:
    def __init__(self, index, timestamp, data, prev_hash, hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.prev_hash = prev_hash
        self.hash = hash
        
    @staticmethod
    def calculate_hash(index, timestamp, data, prev_hash):
        concatenated = str(index) + str(prev_hash) + str(timestamp) + str(data)
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()
    
class BlockChain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        
    def create_genesis_block(self):
        return Block(0, int(time.time()), "Genesis Block", "0", Block.calculate_hash(0, int(time.time()), "Genesis Block", "0"))

    def add_block(self, data):
        previous_block = self.chain[-1]
        
        index = previous_block.index + 1
        timestamp = int(time.time())
        prev_hash = previous_block.hash
        block_hash = Block.calculate_hash(index, timestamp, data, prev_hash)
        
        new_block = Block(index, timestamp, data, prev_hash, block_hash)
        
        self.chain.append(new_block)
        
    def check_hashes(self):
        prev_hash = ""
        for index, block in enumerate(self.chain):
            if index == 0:
                continue
            prev_hash = "" if index < 1 else self.chain[index - 1].hash
            if (block.hash != block.calculate_hash(block.index, block.timestamp, block.data, prev_hash)):
                return False
        return True
        

chain = BlockChain()

chain.add_block("1")
chain.add_block("2")
chain.add_block("3")
chain.add_block("4")
chain.add_block("5")

print(f"Blockchain is {"valid" if chain.check_hashes() else "invalid"}")