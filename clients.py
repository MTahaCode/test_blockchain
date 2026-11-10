from enum import Enum

class Clients(Enum):
    # name = (url, number of seed blocks to start with)
    jack = ("http://localhost:5000", 3)
    tony = ("http://localhost:5001", 1)

    def __init__(self, url, seed_blocks):
        self.url = url
        self.seed_blocks = seed_blocks
