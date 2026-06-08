from hashlib import sha256
from typing import List, Tuple

BLOCK_SIZE = 32

class MerkleTree:
    # costruttore classe inizializzato con le foglie
    def __init__(self, leaves: List[bytes]):
        self.leaves = leaves
        self.tree=[leaves] + self.build_tree(leaves)

    def build_tree(self, level: List[bytes]) -> List[List[bytes]]:
        if len(level)==1:
            return []
        
        next_level = []
        for i in range(0, len(level), 2):

            # foglie di numero pari
            if i+1<len(level):
                next_level.append(sha256(level[i]+level[i+1]).digest())
            else: 
                next_level.append(sha256(level[i]+level[i]).digest())

        return [next_level] + self.build_tree(next_level)
    

    # restituisce la radice
    def root(self) -> bytes:
        return self.tree[-1][0]
    

    # restituisce il path dalla foglia-iesima alla root
    def open(self, index: int) ->  Tuple[bytes, List[bytes]]:
        leaf = self.leaves[index]
        path = []
        for level in range(len(self.tree) -1):
            # figlio sx
            if index%2 ==0:
                if index+1 < len(self.tree[level]):
                    sibling = self.tree[level][index+1]
                else:
                    sibling = self.tree[level][index]
            # figlio dx
            else:
                sibling = self.tree[level][index-1]

            path.append(sibling)
            index//=2
        return (leaf, path)

# P divide la codeword in blocchi, hasha ogni blocco e crea il merkel tree
def commit(codeword: bytes) -> bytes:
    chunks = [codeword[i:i+BLOCK_SIZE] for i in range(0, len(codeword), BLOCK_SIZE)]
    leaves = [ sha256(chunk).digest() for chunk in chunks]
    tree = MerkleTree(leaves)
    return tree.root()

# V riceve la foglia e il path, e deve ricalcolare l'hash salendo fino alla radice.
def verify_proof(root: bytes, index: int, leaf: bytes, proof: List[bytes]) -> bool:
    node = leaf
    for sibling in proof:
        if index % 2 == 0:
            node = sha256(node + sibling).digest()
        else:
            node = sha256(sibling + node).digest()
        index //= 2
    return node == root

# V riceve la root e le risposte di P
def verify_queries(root: bytes, queries: List[Tuple[int, bytes, List[bytes]]]) -> bool:

    for index, leaf, proof in queries:
        if not verify_proof(root, index, leaf, proof):
            return False
    return True



