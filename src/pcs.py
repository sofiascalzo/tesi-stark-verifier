from hashlib import sha256
from math import log2
from typing import List, Tuple

from field import FieldElement, two_adic_generator
from polynomial import coset_lde
from merkle_tree import MerkleTree, verify_proof
from challenger import Challenger
from fri_parameters import FriParameters
from fri import fri_prove, fri_verify, FriProof

class ProverData:
    """
    the full codeword of f and its Merkle tree
    """
    def __init__(self, codeword: List[FieldElement], tree: MerkleTree):
        self.codeword = codeword
        self.tree = tree

class FOpening:
    """
    one opening of the committed f
    """
    def __init__(self, lo_value: FieldElement, hi_value: FieldElement, lo_path: List[bytes], hi_path: List[bytes]):
        self.lo_value = lo_value
        self.hi_value = hi_value
        self.lo_path = lo_path
        self.hi_path = hi_path


class OpeningProof:from hashlib import sha256
from math import log2
from typing import List, Tuple

from field import FieldElement, two_adic_generator
from polynomial import coset_lde
from merkle_tree import MerkleTree, verify_proof
from challenger import Challenger
from fri_parameters import FriParameters
from fri import fri_prove, fri_verify, FriProof

class ProverData:
    """
    the full codeword of f and its Merkle tree
    """
    def __init__(self, codeword: List[FieldElement], tree: MerkleTree):
        self.codeword = codeword
        self.tree = tree

class FOpening:
    """
    one opening of the committed f
    """
    def __init__(self, lo_value: FieldElement, hi_value: FieldElement, lo_path: List[bytes], hi_path: List[bytes]):
        self.lo_value = lo_value
        self.hi_value = hi_value
        self.lo_path = lo_path
        self.hi_path = hi_path


class OpeningProof:
    """
    full evaluation proof sent to the verifier
    """
    def __init__(self, fri_proof: FriProof, f_openings: List[FOpening]):
        self.fri_proof = fri_proof
        self.f_openings = f_openings


def _quotient(f_coeffs: List[FieldElement], z: FieldElement, v: FieldElement) -> List[FieldElement]:
    """
    compute q(X) = (f(X) - v) / (X - z)
    """
    a = list(f_coeffs)

    # a(X) = f(X) - v
    a[0] = a[0] - v

    d = len(a) - 1   # grado di a
    q = [FieldElement(0) for _ in range(d)]   

    # division by (x-z)
    #   q[d-1] = a[d]
    #   q[i-1] = a[i] + z * q[i]      for i = d-1 .. 1
    q[d-1] = a[d]
    for i in range(d-1, 0, -1):
        q[i-1] = a[i] + z * q[i]

    # pad q to the original power of two length
    q = q + [FieldElement(0)] * (len(f_coeffs) - len(q))
    return q


def _derive_query_indices(fri_proof: FriProof, params: FriParameters, poly_len: int) -> List[int]:
    """
    derive the FRI query indices by replaying the Fiat-Shamir transcript, exactly the way fri_verify does. Both sides therefore agree on the same positions
    """
    ch = Challenger()
    params.observe_into(ch)

    for root in fri_proof.roots:
        ch.observe_bytes(root)
        ch.sample_ext_field()

    final_poly_bytes = b''.join(c.to_bytes() for c in fri_proof.final_poly)
    ch.observe_bytes(final_poly_bytes)


    extended_n = params.blowup() * poly_len
    return ch.sample_indices(params.num_queries, extended_n // 2)


def _domain_params(params: FriParameters, poly_len: int):
    """
    return (omega, g, extended_n) describing the LDE coset domain
    """
    extended_n = params.blowup() * poly_len
    log_ext = int(log2(extended_n))

    omega = two_adic_generator(log_ext)        # generatore del subgroup di ordine N
    g = two_adic_generator(log_ext + 1)        # coset shift
    return omega, g, extended_n


# commit - open - verify

def commit(f_coeffs: List[FieldElement], params: FriParameters) -> Tuple[bytes, ProverData]:
    """
    evaluate f on the LDE coset, Merkle-hash it, and return (root, prover_data)
    """
    poly_len = len(f_coeffs)
    assert poly_len > 0 and (poly_len & (poly_len - 1) == 0), f"Polynomial length must be a power of two and greater than zero, got {poly_len}"

    codeword = coset_lde(f_coeffs, params.log_blowup)
    leaves = [sha256(val.to_bytes()).digest() for val in codeword]   
    tree = MerkleTree(leaves)
    return tree.root(), ProverData(codeword, tree)


def open_at(f_coeffs: List[FieldElement], prover_data: ProverData, z: FieldElement, v: FieldElement, params: FriParameters) -> OpeningProof:
    """
    1. build the quotient q = (f - v) / (X - z)
    2. run FRI on q to prove it is low-degree and commit to its codeword
    3. derive FRI query indices and open the committed f
    """
    poly_len = len(f_coeffs)
    _, g, extended_n = _domain_params(params, poly_len)

    # z fuori dall'evaluation domain, altrimenti il quoziente non e' definito
    # z is in the coset domain se e solo se z^N == g^N (qui g^N = -1)
    if z**extended_n == g**extended_n:
        raise ValueError(f"z = {z} is in the coset domain, cannot compute the quotient")

    # 1. quotient
    q_coeffs = _quotient(f_coeffs, z, v)

    # 2. FRI proof su q
    fri_ch = Challenger()
    params.observe_into(fri_ch)
    fri_proof = fri_prove(q_coeffs, params, fri_ch)

    # 3. open f nella stessa posizione di query usata da FRI
    indices = _derive_query_indices(fri_proof, params, poly_len)
    half = extended_n // 2
    f_openings = []
    for q_idx in indices:
        lo_idx = q_idx % half
        hi_idx = lo_idx + half
        _, lo_path = prover_data.tree.open(lo_idx)
        _, hi_path = prover_data.tree.open(hi_idx)
        f_openings.append(FOpening(prover_data.codeword[lo_idx], prover_data.codeword[hi_idx], lo_path, hi_path))

    return OpeningProof(fri_proof, f_openings)


def verify(commitment_root: bytes, z: FieldElement, v: FieldElement, opening_proof: OpeningProof, params: FriParameters, poly_len: int) -> bool:
    """
    accept if `commitment_root` satisfies f(z) = v
    """

    fri_ch = Challenger()
    params.observe_into(fri_ch)
    if not fri_verify(opening_proof.fri_proof, params, fri_ch, poly_len):
        return False

    # ricostruisci le posizioni della query
    indices = _derive_query_indices(opening_proof.fri_proof, params, poly_len)
    omega, g, extended_n = _domain_params(params, poly_len)
    half = extended_n // 2
    if len(opening_proof.f_openings) != len(indices):
        return False

    for k, q_idx in enumerate(indices):
        lo_idx = q_idx % half
        hi_idx = lo_idx + half
        fo = opening_proof.f_openings[k]

        # i valori di f appartengono al commitment root
        lo_leaf = sha256(fo.lo_value.to_bytes()).digest()
        hi_leaf = sha256(fo.hi_value.to_bytes()).digest()
        if not (verify_proof(commitment_root, lo_idx, lo_leaf, fo.lo_path) and verify_proof(commitment_root, hi_idx, hi_leaf, fo.hi_path)):
            return False

        # i valori di q
        q_lo = opening_proof.fri_proof.query_proofs[k].rounds[0].lo_value
        q_hi = opening_proof.fri_proof.query_proofs[k].rounds[0].hi_value

        # i punti x_lo, x_hi = g * omega^idx
        x_lo = g * (omega ** lo_idx)
        x_hi = g * (omega ** hi_idx)  

        # q(x) * (x - z) == f(x) - v
        if q_lo * (x_lo - z) != fo.lo_value - v:
            return False
        if q_hi * (x_hi - z) != fo.hi_value - v:
            return False

    return True
    """
    full evaluation proof sent to the verifier
    """
    def __init__(self, fri_proof: FriProof, f_openings: List[FOpening]):
        self.fri_proof = fri_proof
        self.f_openings = f_openings


def _quotient(f_coeffs: List[FieldElement], z: FieldElement, v: FieldElement) -> List[FieldElement]:
    """
    compute q(X) = (f(X) - v) / (X - z)
    """
    a = list(f_coeffs)

    # a(X) = f(X) - v
    a[0] = a[0] - v

    d = len(a) - 1   # grado di a
    q = [FieldElement(0) for _ in range(d)]  

    # division by (x-z)
    #   q[d-1] = a[d]
    #   q[i-1] = a[i] + z * q[i]      for i = d-1 .. 1
    q[d-1] = a[d]
    for i in range(d-1, 0, -1):
        q[i-1] = a[i] + z * q[i]

    # pad q to the original power of two length
    q = q + [FieldElement(0)] * (len(f_coeffs) - len(q))
    return q


def _derive_query_indices(fri_proof: FriProof, params: FriParameters, poly_len: int) -> List[int]:
    """
    derive the FRI query indices by replaying the Fiat-Shamir transcript, exactly the way fri_verify does. Both sides therefore agree on the same positions
    """
    ch = Challenger()
    params.observe_into(ch)

    for root in fri_proof.roots:
        ch.observe_bytes(root)
        ch.sample_ext_field()

    final_poly_bytes = b''.join(c.to_bytes() for c in fri_proof.final_poly)
    ch.observe_bytes(final_poly_bytes)

    extended_n = params.blowup() * poly_len
    return ch.sample_indices(params.num_queries, extended_n // 2)


def _domain_params(params: FriParameters, poly_len: int):
    """
    return (omega, g, extended_n) describing the LDE coset domain
    """
    extended_n = params.blowup() * poly_len
    log_ext = int(log2(extended_n))
    omega = two_adic_generator(log_ext)        # generatore del subgroup di ordine N
    g = two_adic_generator(log_ext + 1)        # coset shift
    return omega, g, extended_n


# commit - open - verify

def commit(f_coeffs: List[FieldElement], params: FriParameters) -> Tuple[bytes, ProverData]:
    """
    evaluate f on the LDE coset, Merkle-hash it, and return (root, prover_data)
    """
    poly_len = len(f_coeffs)
    assert poly_len > 0 and (poly_len & (poly_len - 1) == 0), f"Polynomial length must be a power of two and greater than zero, got {poly_len}"

    codeword = coset_lde(f_coeffs, params.log_blowup)
    leaves = [sha256(val.to_bytes()).digest() for val in codeword]  
    tree = MerkleTree(leaves)
    return tree.root(), ProverData(codeword, tree)


def open_at(f_coeffs: List[FieldElement], prover_data: ProverData, z: FieldElement, v: FieldElement, params: FriParameters) -> OpeningProof:
    """
    1. build the quotient q = (f - v) / (X - z)
    2. run FRI on q to prove it is low-degree and commit to its codeword
    3. derive FRI query indices and open the committed f
    """
    poly_len = len(f_coeffs)
    _, g, extended_n = _domain_params(params, poly_len)

    # z fuori dall'evaluation domain, altrimenti il quoziente non e' definito
    # z is in the coset domain se e solo se z^N == g^N (qui g^N = -1)
    if z**extended_n == g**extended_n:
        raise ValueError(f"z = {z} is in the coset domain, cannot compute the quotient")

    # 1. quotient
    q_coeffs = _quotient(f_coeffs, z, v)

    # 2. FRI proof su q
    fri_ch = Challenger()
    params.observe_into(fri_ch)
    fri_proof = fri_prove(q_coeffs, params, fri_ch)

    # 3. open f nella stessa posizione di query usata da FRI
    indices = _derive_query_indices(fri_proof, params, poly_len)
    half = extended_n // 2
    f_openings = []
    for q_idx in indices:
        lo_idx = q_idx % half
        hi_idx = lo_idx + half
        _, lo_path = prover_data.tree.open(lo_idx)
        _, hi_path = prover_data.tree.open(hi_idx)
        f_openings.append(FOpening(prover_data.codeword[lo_idx], prover_data.codeword[hi_idx], lo_path, hi_path))

    return OpeningProof(fri_proof, f_openings)


def verify(commitment_root: bytes, z: FieldElement, v: FieldElement, opening_proof: OpeningProof, params: FriParameters, poly_len: int) -> bool:
    """
    accept if `commitment_root` satisfies f(z) = v
    """
    # FRI: quoziente di grado basso
    fri_ch = Challenger()
    params.observe_into(fri_ch)
    if not fri_verify(opening_proof.fri_proof, params, fri_ch, poly_len):
        return False

    # ricostruisci le posizioni della query
    indices = _derive_query_indices(opening_proof.fri_proof, params, poly_len)
    omega, g, extended_n = _domain_params(params, poly_len)
    half = extended_n // 2
    if len(opening_proof.f_openings) != len(indices):
        return False

    for k, q_idx in enumerate(indices):
        lo_idx = q_idx % half
        hi_idx = lo_idx + half
        fo = opening_proof.f_openings[k]

        # i valori di f appartengono al commitment root
        lo_leaf = sha256(fo.lo_value.to_bytes()).digest()
        hi_leaf = sha256(fo.hi_value.to_bytes()).digest()
        if not (verify_proof(commitment_root, lo_idx, lo_leaf, fo.lo_path) and verify_proof(commitment_root, hi_idx, hi_leaf, fo.hi_path)):
            return False

        # i valori di q
        q_lo = opening_proof.fri_proof.query_proofs[k].rounds[0].lo_value
        q_hi = opening_proof.fri_proof.query_proofs[k].rounds[0].hi_value

        # i punti x_lo, x_hi = g * omega^idx
        x_lo = g * (omega ** lo_idx)
        x_hi = g * (omega ** hi_idx)  

        # q(x) * (x - z) == f(x) - v
        if q_lo * (x_lo - z) != fo.lo_value - v:
            return False
        if q_hi * (x_hi - z) != fo.hi_value - v:
            return False

    return True