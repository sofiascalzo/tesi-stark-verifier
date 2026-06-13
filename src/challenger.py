from typing import List
from field import FieldElement, BABYBEAR_PRIME
from extension import ExtFieldElement
from keccak import keccak_f

class Challenger:

    # stato della sponge: 200 bytes = 25 lane
    # i primi 136 bytes (17 lane) sono il rate
    # gli ultimi 64 bytes (8 lane) sono la capacity (segreto)

    def __init__(self):
        self.state = [0] * 25       # 25 celle di stato
        self.absorb_pos = 0         # posizione nel rate
        self.squeezing = False      # modalità corrente
        self.squeeze_pos = 0

    # legge dati pubblici di P, e aggiorna lo stato (CanObserve<G>)
    def observe_bytes(self, data: bytes):
        # se stavamo leggendo (squeeze), torniamo in modalita' scrittura
        if self.squeezing:
            self.squeezing = False

        for byte in data:
            # XOR il byte nella posizione corrente del rate
            # ogni lane ha 8 bytes, quindi lane = posizione / 8
            lane = self.absorb_pos // 8
            offset = (self.absorb_pos % 8) * 8
            self.state[lane] ^= byte << offset
            self.absorb_pos += 1

            #quando il rate e' pieno, permuta e ricomincia
            if self.absorb_pos == 136:    # rate pieno
                self.state = keccak_f(self.state)
                self.absorb_pos = 0

    # converte un elementto in Fp in intero a 4 bytes 
    def observe_field(self, value: int): 
        self.observe_bytes(value.to_bytes(4, 'little'))


    def sample(self) -> int:
        # da scrittura a letture
        if not self.squeezing:
            # padding Keccak: 0x1F alla posizione corrente, 0x80 al byte 135
            # applica il padding Keccak per marcare la fine dei dati
            # 0x1F alla posizione corrente 

            lane = self.absorb_pos // 8
            offset = (self.absorb_pos % 8) * 8
            self.state[lane] ^= 0x1F << offset
            # 0x80 all'ultimo byte del rate
            self.state[16] ^= 0x80 << 56 

            #permuta rate e capacity insieme     
            self.state = keccak_f(self.state)
            self.absorb_pos = 0
            self.squeezing = True
            self.squeeze_pos = 0

        #leggi 32 bytes dal rate
        output = bytearray(32)
        for i in range(32):

            #se il rate e' esaurito, permuta per generare altri bytes
            if self.squeeze_pos >= 136:
                self.state = keccak_f(self.state)
                self.squeeze_pos = 0

             #estrai un byte dalla cella corrente
            lane = self.squeeze_pos // 8
            offset = (self.squeeze_pos % 8) * 8
            output[i] = (self.state[lane] >> offset) & 0xFF
            self.squeeze_pos += 1
        return bytes(output)


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
        
    # usato per i challenge alpha, estratto da Babybear^4
    def sample_ext_field(self) -> ExtFieldElement:
        
        # # 32 bytes dal rate: Keccak squeeze
        raw = self.sample()
        c0= FieldElement(int.from_bytes(raw[:4], 'little'))
        c1= FieldElement(int.from_bytes(raw[4:8], 'little'))
        c2= FieldElement(int.from_bytes(raw[8:12], 'little'))
        c3= FieldElement(int.from_bytes(raw[12:16], 'little'))

        return ExtFieldElement([c0,c1,c2,c3])
        
