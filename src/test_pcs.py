from field import FieldElement
from polynomial import evaluate
from fri_parameters import FriParameters
from pcs import commit, open_at, verify

params = FriParameters(log_blowup=1, num_queries=20, proof_of_work_bits=0, final_poly_len=2)

# f(X) = 1 + 2X + 3X^2 + ...
f = [FieldElement(c) for c in [1, 2, 3, 4, 5, 6, 7, 8]]

# evaluation point outside the domain
z = FieldElement(1234567)
v = evaluate(f, z)

root, prover_data = commit(f, params)


# an honest opening is accepted
proof = open_at(f, prover_data, z, v, params)
assert verify(root, z, v, proof, params, len(f)) is True
print("honest prover: accepted")


# a wrong claimed value is rejected
v_wrong = v + FieldElement(1)
proof_wrong = open_at(f, prover_data, z, v_wrong, params)
assert verify(root, z, v_wrong, proof_wrong, params, len(f)) is False
print("wrong value: rejected")


# a tampered opening is rejected
proof_tampered = open_at(f, prover_data, z, v, params)
proof_tampered.f_openings[0].lo_value = FieldElement(999999)
assert verify(root, z, v, proof_tampered, params, len(f)) is False
print("tampered opening: rejected")