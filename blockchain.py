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
    
    def getJson(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "prev_hash": self.prev_hash,
            "hash": self.hash
        }
    
class BlockChain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        
    def create_genesis_block(self):
        return Block(0, 0, "Genesis Block", "0", Block.calculate_hash(0, 0, "Genesis Block", "0"))

    def add_block(self, data):
        previous_block = self.chain[-1]
        
        index = previous_block.index + 1
        timestamp = int(time.time())
        prev_hash = previous_block.hash
        block_hash = Block.calculate_hash(index, timestamp, data, prev_hash)
        
        new_block = Block(index, timestamp, data, prev_hash, block_hash)
        
        self.chain.append(new_block)
        
        return new_block

    def add_received_block(self, block):
        self.chain.append(block)
        return block

    def load_chain(self, blocks):
        self.chain = blocks

    def get_hashes(self):
        return [block.hash for block in self.chain]

    def find_common_ancestor(self, other_hashes):
        # Newest block of ours whose hash is also in the other chain
        other_hashes = set(other_hashes)
        for block in reversed(self.chain):
            if block.hash in other_hashes:
                return block
        return None

    def is_valid_branch(self, branch):
        if not branch:
            return False

        # The first block's parent must be in our chain, at the position right before it
        previous = None
        for block in self.chain:
            if block.hash == branch[0].prev_hash:
                previous = block
                break
        if previous is None:
            return False

        # Every block must have a correct hash and link to the one before it
        for block in branch:
            if block.index != previous.index + 1:
                return False
            if block.prev_hash != previous.hash:
                return False
            if block.hash != Block.calculate_hash(block.index, block.timestamp, block.data, block.prev_hash):
                return False
            previous = block

        return True

    def replace(self, branch):
        # The branch's first block points to its parent; find that parent in our chain,
        # keep everything up to it and replace the rest with the branch
        for index, block in enumerate(self.chain):
            if block.hash == branch[0].prev_hash:
                self.chain = self.chain[:index + 1] + branch
                return True
        return False

    def add_seed_blocks(self, count):
        # Deterministic blocks (timestamp = index) so every node seeds identical blocks
        for _ in range(count):
            previous_block = self.chain[-1]
            index = previous_block.index + 1
            data = f"Seed block {index}"
            block_hash = Block.calculate_hash(index, index, data, previous_block.hash)
            self.chain.append(Block(index, index, data, previous_block.hash, block_hash))

    def check_hashes(self):
        prev_hash = ""
        for index, block in enumerate(self.chain):
            if index == 0:
                continue
            prev_hash = "" if index < 1 else self.chain[index - 1].hash
            if (block.hash != block.calculate_hash(block.index, block.timestamp, block.data, prev_hash)):
                return False
        return True
    
    def getJson(self):
        return [
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "data": block.data,
                "prev_hash": block.prev_hash,
                "hash": block.hash
            }
            for block in self.chain
        ]
        

if __name__ == "__main__":
    chain = BlockChain()

    chain.add_block("1")
    chain.add_block("2")
    chain.add_block("3")
    chain.add_block("4")
    chain.add_block("5")

    print(f"Blockchain is {"valid" if chain.check_hashes() else "invalid"}")