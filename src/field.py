
BABYBEAR_PRIME = (1<<31) - (1<<27) + 1
TWO_ADICITY = 27
MULTIPLICATIVE_GENERATOR = 31


class FieldElement:

    def __init__(self, value: int):
        self.value = value % BABYBEAR_PRIME

    def __add__(self, other):
        # cosi` prova il metodo reversed di ExtFieldElement
        if not isinstance(other, FieldElement):
            return NotImplemented
        return FieldElement(self.value + other.value)

    def __sub__(self, other):
        if not isinstance(other, FieldElement):
            return NotImplemented
        return FieldElement(self.value - other.value)

    def __mul__(self, other):
        if not isinstance(other, FieldElement):
            return NotImplemented
        return FieldElement(self.value * other.value)

    def __neg__(self):
        return FieldElement(-self.value)

    def __eq__(self, other):
        if isinstance(other, FieldElement):
            return self.value == other.value
        return False

    def __repr__(self):
        return f"F({self.value})"

    def __pow__(self, exp):
        # per omega ** i nel test e due nel fold (inv usa Fermat)
        return FieldElement(pow(self.value, exp, BABYBEAR_PRIME))

    def inverse(self):
        assert self.value != 0, "cannot invert zero"
        return FieldElement(pow(self.value, BABYBEAR_PRIME - 2, BABYBEAR_PRIME))

    def to_bytes(self) -> bytes:
        return self.value.to_bytes(4, 'little')

# precalcolo omega 
TWO_ADIC_GENERATORS = [ FieldElement(pow(MULTIPLICATIVE_GENERATOR, (BABYBEAR_PRIME - 1) >> k, BABYBEAR_PRIME)) for k in range(TWO_ADICITY + 1)]


# restituisce le radici dell'unità ovvero omwga^0, omega^1 ... -> il sottogruppo di 2^k e` generato da two_adic_generator(k)
def two_adic_generator(bits: int) -> int:
    assert bits <= TWO_ADICITY, f"bits={bits} > TWO_ADICITY={TWO_ADICITY}"
    return TWO_ADIC_GENERATORS[bits]