from field import FieldElement, BABYBEAR_PRIME
from typing import List

# 11 e` il termine noto del polinomio irriducibile su BabyBear: X⁴ - 11  (
# infatti 11 non è una quarta potenza nel campo -->  e` un'estensione valida di grado 4.

W = FieldElement(11)

class ExtFieldElement:
    def __init__(self, coeffs: List[FieldElement]):
        assert len(coeffs) == 4, "coeffs must have length 4"
        self.coeffs = coeffs

    def __add__(self, other):
        if isinstance(other, FieldElement):
            return ExtFieldElement([self.coeffs[0] + other, self.coeffs[1], self.coeffs[2], self.coeffs[3]])
        return ExtFieldElement([a + b for a, b in zip(self.coeffs, other.coeffs)])

    def __sub__(self, other):
        if isinstance(other, FieldElement):
            return ExtFieldElement([self.coeffs[0] - other, self.coeffs[1], self.coeffs[2], self.coeffs[3]])
        return ExtFieldElement([a - b for a, b in zip(self.coeffs, other.coeffs)])

    def __mul__(self, other):
        if isinstance(other, FieldElement):
            return ExtFieldElement([c * other for c in self.coeffs])
        
        
        a0, a1, a2, a3 = self.coeffs
        b0, b1, b2, b3 = other.coeffs

        # riduzione -> sostituisco X^4 con W=11
        # costante + X^4 diventa W
        # X + X^5 diventa W·X
        # X^2 + X^6 diventa W·X²
        # X^3 resta
        c0 = a0 * b0 + W * (a1 * b3 + a2 * b2 + a3 * b1)
        c1 = a0 * b1 + a1 * b0 + W * (a2 * b3 + a3 * b2)
        c2 = a0 * b2 + a1 * b1 + a2 * b0 + W * (a3 * b3)
        c3 = a0 * b3 + a1 * b2 + a2 * b1 + a3 * b0
        return ExtFieldElement([c0, c1, c2, c3])


    def __neg__(self):
        return ExtFieldElement([-c for c in self.coeffs])

    def __eq__(self, other):
        if isinstance(other, ExtFieldElement):
            return all(a == b for a, b in zip(self.coeffs, other.coeffs))
        return False

    def __repr__(self):
        return f"ExtF({', '.join(repr(c) for c in self.coeffs)})"
    
    def __pow__(self, exp: int):
        # esponenziazione binaria (square and multiply)
        result = ExtFieldElement([FieldElement(1), FieldElement(0), FieldElement(0), FieldElement(0)]) # 1 nel campo esteso
        base = self
        while exp > 0:
            if exp & 1:
                result = result * base
            base = base * base
            exp >>= 1
        return result
    # FieldElement OP ExtFieldElement

    def __radd__(self, other):
        if isinstance(other, FieldElement):
            return ExtFieldElement([other + self.coeffs[0], self.coeffs[1], self.coeffs[2], self.coeffs[3]])

    def __rsub__(self, other):
        if isinstance(other, FieldElement):
            return ExtFieldElement([other - self.coeffs[0], -self.coeffs[1], -self.coeffs[2], -self.coeffs[3]])
        

    def __rmul__(self, other):
        if isinstance(other, FieldElement):
            return ExtFieldElement([c * other for c in self.coeffs])
        

    def inverse(self):
        # piccolo teorema di Fermat nel campo esteso:
        # a^(-1) = a^(p^4 - 2)
        assert any(c.value != 0 for c in self.coeffs), "cannot invert zero"
        return self ** (BABYBEAR_PRIME ** 4 - 2)

    def to_bytes(self) -> bytes:
        return b''.join(c.to_bytes() for c in self.coeffs)