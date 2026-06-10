from hashlib import sha256
from typing import List
from field import FieldElement, BABYBEAR_PRIME

class Challenger:

    def __init__(self):
        # Lo stato iniziale e' un hash vuoto. La domain separation avviene
        # osservando la configurazione del protocollo come primo passo.
        self.state = sha256(b"").digest()

    # legge dati pubblici di P, e aggiorna lo stato (CanObserve<G>)
    def observe_bytes(self, data: bytes):
        self.state = sha256(self.state + data).digest()

    # converte un elementto in Fp in intero a 4 bytes 
    def observe_field(self, value: int): 
        self.observe_bytes(value.to_bytes(4, 'little'))

    # random alfa
    def sample(self) -> bytes:
        challenge = self.state
        
        self.state = sha256(self.state).digest()
        return challenge

    def sample_field(self) -> int:
        # ottiene random
        raw = self.sample()
        # lo converte in intero in Fp
        return FieldElement(int.from_bytes(raw, 'big'))


    # domain_size è la dimensione del dominio della codeword (blowup * size_dominio_polinomio)
    def sample_indices(self, num_queries: int, domain_size: int) -> List[int]:
            indices = []
            for _ in range(num_queries):
                raw = self.sample()
                index = int.from_bytes(raw, 'big') % domain_size
                indices.append(index)
            return indices

    # Proof-of-work: trova un nonce tale che H(state || nonce) abbia 'bits' zeri iniziali.
    def grind(self, bits: int) -> int:
        pass
        
        
