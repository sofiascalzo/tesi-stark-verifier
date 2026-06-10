from typing import List
from math import log2
from field import FieldElement, two_adic_generator

# n*log(n) algoritmo, dimezza il problema ricorsivamente sfrtuttando la simmetria F(x) = f_even(X²) + X · f_odd(X²)

# ritorna le valutazioni su su omega^i : F(ω^i) i[0,n-1]
def ntt(coeffs:List[FieldElement], omega: FieldElement) -> List[FieldElement]:
    n=len(coeffs)

    # polinomio costante
    if n==1:
        return coeffs[:]
    
    omega_sq = omega * omega
    even = ntt(coeffs[0::2], omega_sq)
    odd = ntt(coeffs[1::2], omega_sq)

    result = [FieldElement(0)] * n
    w=FieldElement(1) # omega0
    for i in range(n//2):
        second_term = w * odd[i]
        result[i] = even[i] + second_term
        result[i + n // 2] = even[i] - second_term
        w = w * omega

    return result

# valutazioni -> coefficienti che producono quelle valutazioni con omega^-1, diviso tutto per n
# usato prima di LDE
def intt(evals: List[FieldElement], omega: FieldElement) -> List[FieldElement]:

    n=len(evals)
    omega_inv= omega.inverse()
    ntt_coeffs = ntt(evals, omega_inv)
    n_inv = FieldElement(pow(n, BABYBEAR_PRIME - 2, BABYBEAR_PRIME))
    
    coeffs = []
    for c in ntt_coeffs:
        coeffs.append(c * n_inv)

    return coeffs




# valutazione puntuale
def evaluate(coeffs: List[FieldElement], point: FieldElement) -> FieldElement:
    result = FieldElement(0)
    for c in reversed(coeffs):
        result = result * point + c
    return result

# low degree extension su coset, ritorna le valutazioni sul coset di dimensione 2^log_blowup * n
# questa e` la codeword Reed-Solomon che viene committata nel Merkle Tree
def coset_lde(coeffs: List[FieldElement], log_blowup: int) -> List[FieldElement]:
    n= len(coeffs)
    blowup = 1 << log_blowup
    extended_n = blowup * n

    log_extended_n = int(log2(extended_n))
    omega = two_adic_generator(log_extended_n)

    # g: coset shift {g, g*omega, g*omega^2, ...}
    g=two_adic_generator(log_extended_n+1)

    # padding di 0 fino alla prossima potenza di n
    padded = coeffs + [FieldElement(0)] * (extended_n - n)

    extended_evaluations = [FieldElement(0)] * extended_n
    g_power =FieldElement(1)
    for i in range(extended_n):
        extended_evaluations[i]=padded[i] * g_power
        g_power = g_power * g

    return ntt(extended_evaluations, omega)
