from hashlib import sha256
from typing import List, Tuple
from math import log2

from polynomial import ntt, intt, evaluate, coset_lde
from field import BABYBEAR_PRIME, add, sub, mul, neg, inv, two_adic_generator
from merkle_tree import MerkleTree, verify_proof
from challenger import Challenger
from fri_parameters import FriParameters

# risposta di P a una query per un round
class QueryRound:

    def __init__(self, lo_value: int, hi_value: int, lo_path: List[bytes], hi_path: List[bytes]):
        self.lo_value = lo_value
        self.hi_value = hi_value
        self.lo_path = lo_path
        self.hi_path = hi_path


# risposta di P per una query di tutti i round
class QueryProof:

    def __init__(self, rounds: List[QueryRound]):
        self.rounds = rounds

# la prova che P invia a V
class FriProof:
    def __init__(self, roots: List[bytes], final_poly: List[int],
                 query_proofs: List[QueryProof]):
        self.roots = roots
        self.final_poly = final_poly
        self.query_proofs = query_proofs

    # stato interno di P per round, visibile solo a P
class RoundState:

    def __init__(self, codeword: List[int], tree: MerkleTree,
                omega: int, offset: int):
        self.codeword = codeword
        self.tree = tree
        self.omega = omega
        self.offset = offset




# - codeword[i]        = f(x_i)      dove x_i = offset * omega^i
# - codeword[i + N/2]  = f(-x_i)     perche' omega^(N/2) = -1
# - f_even = (f(x) + f(-x)) / 2
# - f_odd  = (f(x) - f(-x)) / (2*x)
# - f'(x^2) = f_even + alpha * f_odd
def fold(codeword: List[int], alpha: int, offset:int, omega:int) -> List[int]:
    n = len(codeword)
    two_inv = inv(2)
    folded = []

    x_i = offset # w0
    for i in range(n//2):
        lo = codeword[i]
        hi = codeword[i + n//2]

        f_even = mul(add(lo,hi), two_inv)
        f_odd = mul(sub(lo,hi),mul(two_inv, inv(x_i)))
        folded.append(add(f_even, mul(alpha, f_odd)))

        x_i = mul(x_i, omega)

    return folded

# crea la codeword e ogni round committa nel Merkle tree, riceve alpha dal Challenger, folda
def commit_phase(poly_coeffs: List[int], params: FriParameters, challenger: Challenger) -> Tuple[List[RoundState], List[int], List[int]]:

    n=len(poly_coeffs)
    extended_n = params.blowup()*n
    log_extended_n = int(log2(extended_n))

    omega = two_adic_generator(log_extended_n)
    offset = two_adic_generator(log_extended_n +1)

    # crea codeword con lde
    codeword = coset_lde(poly_coeffs, params.log_blowup)

    round_states = []
    alphas = []

    # folding 
    # (se final_poly_len = 1 piu folding ma invio un coeff, final_poly_len = 2 prova piu piccola ma piccola ma invio 2 coeff)
    while len(codeword) > params.final_poly_len:
        # hash di ogni elemento e estrare la root
        leaves = [sha256(v.to_bytes(4, 'little')).digest() for v in codeword]
        tree = MerkleTree(leaves)
        root =tree.root()
        round_states.append(RoundState(codeword,tree,omega,offset))

        # registro la root nel transcript
        challenger.observe_bytes(root)
        # challenge
        alpha = challenger.sample_field()
        alphas.append(alpha)

        #fold
        codeword = fold(codeword, alpha, offset,omega)

        # aggiorna dominio
        offset =mul(offset, offset)
        omega = mul(omega, omega)

    #mandato in chiaro perche` l'ultimo
    final_poly = codeword

    final_poly_bytes = b''.join(v.to_bytes(4, 'little') for v in final_poly) 
    # registro anche il polinomio finale nel transcript
    challenger.observe_bytes(final_poly_bytes)

    return round_states, final_poly, alphas

# il challenger sceglie indici random, il prover apre i Merkle path a quegli indici per ogni round
def query_phase(round_states: List[RoundState], params: FriParameters, challenger: Challenger) -> List[QueryProof]:

    # genera gli indici
    initial_size = len(round_states[0].codeword)
    indices = challenger.sample_indices(params.num_queries, initial_size//2)

    query_proofs = []

    for q in indices:
        rounds = []
        idx = q

        for state in round_states:
            n=len(state.codeword)
            
            # coppie di coefficienti dalle due meta
            lo_idx = idx % (n//2)
            hi_idx = lo_idx + n//2

            # merkle path per ogni coefficiente
            lo_value = state.codeword[lo_idx]
            hi_value = state.codeword[hi_idx]

            lo_leaf, lo_path = state.tree.open(lo_idx)
            hi_leaf, hi_path = state.tree.open(hi_idx)

            rounds.append(QueryRound(lo_value, hi_value, lo_path, hi_path))

            idx = lo_idx

        query_proofs.append(QueryProof(rounds))

    return query_proofs

# P genera la prova completa
def fri_prove(poly_coeffs: List[int], params: FriParameters, challenger: Challenger) -> FriProof:
    round_states, final_poly, alphas = commit_phase(poly_coeffs, params, challenger)
    query_proofs = query_phase(round_states, params, challenger)
    roots=[s.tree.root() for s in round_states]

    return FriProof(roots, final_poly, query_proofs)

# V ha  solo la proof e ricostruisce i challenge dal challenger
def fri_verify(proof: FriProof, params: FriParameters, challenger: Challenger, poly_len: int) -> bool: 
    extended_n = params.blowup() * poly_len
    log_extended_n = int(log2(extended_n))

    omega = two_adic_generator(log_extended_n)
    offset = two_adic_generator(log_extended_n + 1)

    # 1.ricostruisci transcript e alpha
    alphas = []
    omegas = []
    offsets = []
    domain_sizes = []
    current_size = extended_n
    current_omega = omega
    current_offset = offset

    for root in proof.roots:
        domain_sizes.append(current_size)
        omegas.append(current_omega)
        offsets.append(current_offset)

        challenger.observe_bytes(root)
        alpha = challenger.sample_field()
        alphas.append(alpha)

        current_size //= 2
        current_omega = mul(current_omega, current_omega)
        current_offset = mul(current_offset, current_offset)

    # observe final poly
    final_poly_bytes = b''.join(v.to_bytes(4, 'little') for v in proof.final_poly)
    challenger.observe_bytes(final_poly_bytes)

    # 2. ricostruisci indici di quey
    indices = challenger.sample_indices(params.num_queries, extended_n // 2)

    # 3. verifica ongi query (merkle path + colinearity check)
    two_inv = inv(2)
    final_poly_len = len(proof.final_poly)

    for q_idx, qproof in enumerate(proof.query_proofs):
        idx = indices[q_idx]

        for r, qround in enumerate(qproof.rounds):
            n_r = domain_sizes[r]
            half = n_r // 2
            lo_idx = idx % half
            hi_idx = lo_idx + half

            # verifica Merkle path

            lo_leaf = sha256(qround.lo_value.to_bytes(4, 'little')).digest()
            hi_leaf = sha256(qround.hi_value.to_bytes(4, 'little')).digest()

            if not verify_proof(proof.roots[r], lo_idx, lo_leaf, qround.lo_path):
                return False
            if not verify_proof(proof.roots[r], hi_idx, hi_leaf, qround.hi_path):
                return False

            # colinearity check
            x_i = mul(offsets[r], pow(omegas[r], lo_idx, BABYBEAR_PRIME))

            f_even = mul(add(qround.lo_value, qround.hi_value), two_inv)
            f_odd = mul(
                sub(qround.lo_value, qround.hi_value),
                mul(two_inv, inv(x_i))
            )
            expected = add(f_even, mul(alphas[r], f_odd))

            # confronta con il round successivo o con il polinomio finale
            if r < len(qproof.rounds) - 1:
                next_half = domain_sizes[r + 1] // 2
                if lo_idx < next_half:
                    next_value = qproof.rounds[r + 1].lo_value
                else:
                    next_value = qproof.rounds[r + 1].hi_value
                if expected != next_value:
                    return False
            else:
                final_offset = current_offset
                final_omega = current_omega
                final_x = mul(final_offset, pow(final_omega, lo_idx, BABYBEAR_PRIME))
                final_expected = proof.final_poly[lo_idx]
                if expected != final_expected:
                    return False

            idx = lo_idx

    return True

    
    



