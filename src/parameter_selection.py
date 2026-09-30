"""
Measures the FRI proof on the reference implementation and prints two tables:

-Table 1: proof size, for several rates and several security targets
-Table 2: proof size vs prover time, at a fixed security target

"""

import time
import math
from field import FieldElement
from fri_parameters import FriParameters
from fri import fri_prove, fri_verify
from challenger import Challenger


# config
POLY_LEN      = 256              # number of coefficients of the test polynomial
RATES         = [1, 2, 3]       # log_blowup values: rate 1/2, 1/4, 1/8
TARGETS       = [80, 100, 128]  # security targets in bits
FIXED_TARGET  = 100            # target used for the time/size table
REPEATS       = 5            # median over this many runs, to reduce noise

# num query to reach target bits at current blowup
def queries_for(target_bits, log_blowup):
    
    bits_per_query = log_blowup / 2.0
    return math.ceil(target_bits / bits_per_query)


def proof_size_bytes(proof):

    size  = len(proof.roots) * 32    # Merkle roots SHA256
    size += len(proof.final_poly) * 16 # final layer (extension field elements)
    for query in proof.query_proofs:
        for rnd in query.rounds:
            size += 2 * 16   # the two opened values
            size += (len(rnd.lo_path) + len(rnd.hi_path)) * 32  # the two Merkle paths
    return size

# time and size to generate one proof
def run_once(poly_len, log_blowup, num_queries):
    params = FriParameters(log_blowup=log_blowup,
                           num_queries=num_queries,
                           proof_of_work_bits=0,
                           final_poly_len=2)
    poly = [FieldElement((7 * i + 1) % 2013265921) for i in range(poly_len)]

    start = time.perf_counter()
    challenger = Challenger()
    params.observe_into(challenger)
    proof = fri_prove(poly, params, challenger)
    prover_ms = (time.perf_counter() - start) * 1000

    # sanity check: the honest proof must verify
    challenger = Challenger()
    params.observe_into(challenger)
    assert fri_verify(proof, params, challenger, poly_len)

    return prover_ms, proof_size_bytes(proof)


def median_run(poly_len, log_blowup, num_queries):
    times, size = [], None
    for _ in range(REPEATS):
        t, s = run_once(poly_len, log_blowup, num_queries)
        times.append(t)
        size = s   # size is deterministic
    return sorted(times)[REPEATS // 2], size


def table_proof_size():
    print("Table 1: proof size at several rates and security targets")
    for lb in RATES:
        cells = []
        for target in TARGETS:
            q = queries_for(target, lb)
            _, size = median_run(POLY_LEN, lb, q)
            cells.append(f"${size/1024:.0f}$ KB")
        row = f"$\\rho = 1/{2**lb}$ (blowup ${2**lb}$) & " + " & ".join(cells) + r" \\"
        print(row)
    print()


def table_time_size():
    print(f"Table 2: proof size vs prover time, lambda = {FIXED_TARGET}")
    for lb in RATES:
        q = queries_for(FIXED_TARGET, lb)
        t, size = median_run(POLY_LEN, lb, q)
        row = (f"$\\rho = 1/{2**lb}$ & ${2**lb}$ & ${q}$ & "
               f"${t:.0f}$ ms & ${size/1024:.0f}$ KB" + r" \\")
        print(row)
    print()


if __name__ == "__main__":
    print(f"polynomial length: {POLY_LEN}, median of {REPEATS} runs\n")
    table_proof_size()
    table_time_size()