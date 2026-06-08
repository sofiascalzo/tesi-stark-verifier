from challenger import Challenger
from fri_parameters import FriParameters
from fri import fri_prove, fri_verify, FriProof
import field

params = FriParameters(log_blowup=1, num_queries=20, proof_of_work_bits=0, final_poly_len=2)


print("TEST 1: prover onesto")


poly = [1, 2, 3, 4, 5, 6, 7, 8]  # grado 7, 8 coefficienti
print(f"  polinomio: {poly}")
print(f"  grado: {len(poly) - 1}")
print(f"  params: blowup={params.blowup()}, queries={params.num_queries}, final_len={params.final_poly_len}")

p_ch = Challenger()
params.observe_into(p_ch)
proof = fri_prove(poly, params, p_ch)

print(f"  round di folding: {len(proof.roots)}")
print(f"  final_poly: {proof.final_poly}")
print(f"  query proofs: {len(proof.query_proofs)}")

v_ch = Challenger()
params.observe_into(v_ch)
result = fri_verify(proof, params, v_ch, len(poly))

print(f"  RISULTATO: {'ACCETTATA' if result else 'RIFIUTATA'}")
assert result == True, "ERRORE: prova onesta rifiutata!"
print()


# ---


print("\n\nTEST 2: prover disonesto — valore manomesso")


p_ch = Challenger()
params.observe_into(p_ch)
proof = fri_prove(poly, params, p_ch)

original = proof.query_proofs[0].rounds[0].lo_value
proof.query_proofs[0].rounds[0].lo_value = 999999
print(f"  lo_value originale: {original}")
print(f"  lo_value manomesso: 999999")
print(f"  il merkle path non corrisponde piu' all'hash del valore")

v_ch = Challenger()
params.observe_into(v_ch)
result = fri_verify(proof, params, v_ch, len(poly))

print(f"  RISULTATO: {'ACCETTATA' if result else 'RIFIUTATA'}")
assert result == False, "ERRORE: prova manomessa accettata!"
print()


# --- 


print("\n\nTEST 3: prover disonesto — final_poly manomesso")


p_ch = Challenger()
params.observe_into(p_ch)
proof = fri_prove(poly, params, p_ch)

print(f"  final_poly originale: {proof.final_poly}")
proof.final_poly = [42, 42]
print(f"  final_poly manomesso: {proof.final_poly}")
print(f"  il transcript cambia -> gli indici di query cambiano")
print(f"  e il colinearity check all'ultimo round fallisce")

v_ch = Challenger()
params.observe_into(v_ch)
result = fri_verify(proof, params, v_ch, len(poly))

print(f"  RISULTATO: {'ACCETTATA' if result else 'RIFIUTATA'}")
assert result == False, "ERRORE: prova con final_poly manomesso accettata!"
print()


