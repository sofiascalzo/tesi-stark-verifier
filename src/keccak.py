
# serve per troncamento degli interi che superano i 64 bit, funziona come u64
MASK64 = (1 << 64) - 1
 
ROUND_CONSTANTS = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

# https://keccak.team/keccak_specs_summary.html
ROTATION_OFFSETS = [
    [ 0, 36,  3, 41, 18],
    [ 1, 44, 10, 45,  2],
    [62,  6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39,  8, 14],
]
 

def _rot64(x: int, n: int) -> int:
    return ((x << n) | (x >> (64 - n))) & MASK64
 
# 24 round ognuno di 5 step: theta, rho, pi, chi, iota
def keccak_f(state_flat: list) -> list:

    # state_flat: lista di 25 interi a 64 bit.
    # i primi 17 sono il rate (accessibile), gli ultimi 8 sono la capacity (nascosto)
    # flat: state_flat[5*y + x] = 2D: A[x][y]
    A = [[state_flat[5*y + x] for y in range(5)] for x in range(5)]
 
    for rc in ROUND_CONSTANTS:
        # theta: diffusione per colonne
        # calcolo della parità di ogni colonna poi diffusa a quelle adiacenti
        C=[]
        D=[]

        # per ogni colonna x, C[x] = XOR di tutte le celle della colonna x. C[0] = A[0][0] ^ A[0][1] ^ A[0][2] ^ A[0][3] ^ A[0][4]
        for x in range(5):
            C.append(A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4])

        # per ogni colonna x, D[x] = C[x-1] rotato di 1 a sinistra XOR C[x+1]
        for x in range(5):      
            D.append(C[(x-1) % 5] ^ _rot64(C[(x+1) % 5], 1))    

        for x in range(5):
            for y in range(5):
                A[x][y] ^= D[x]
 
        # rho (rotazione bit) + pi (permutazione celle)

        # sposta ogni lane in una posizione diversa della griglia 5×5
        B = [[0]*5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2*x + 3*y) % 5] = _rot64(A[x][y], ROTATION_OFFSETS[x][y])
 
        # chi: non linearità per righe
        A = [[(B[x][y] ^ ((~B[(x+1)%5][y] & MASK64) & B[(x+2)%5][y])) for y in range(5)] for x in range(5)]
 
        # iota: xor a una costante. altrimenti i 24 round sarebbero identici
        A[0][0] ^= rc
 
    # 2D: flat
    return [A[x][y] for y in range(5) for x in range(5)]