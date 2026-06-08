
BABYBEAR_PRIME = (1<<31) - (1<<27) + 1
TWO_ADICITY = 27
MULTIPLICATIVE_GENERATOR = 31

# precalcolo omega 
TWO_ADIC_GENERATORS = [pow(MULTIPLICATIVE_GENERATOR, (BABYBEAR_PRIME - 1) >> k, BABYBEAR_PRIME) for k in range(TWO_ADICITY + 1)]

def add(a: int, b: int) -> int:
    return (a + b) % BABYBEAR_PRIME


def sub(a: int, b: int) -> int:
    return (a - b) % BABYBEAR_PRIME


def mul(a: int, b: int) -> int:
    return (a * b) % BABYBEAR_PRIME


def neg(a: int) -> int:
    return (BABYBEAR_PRIME - a) % BABYBEAR_PRIME


def inv(a: int) -> int:
    assert a != 0, "cannot invert zero"
    return pow(a, BABYBEAR_PRIME - 2, BABYBEAR_PRIME)


# restituisce le radici dell'unità ovvero omwga^0, omega^1 ... -> il sottogruppo di 2^k e` generato da two_adic_generator(k)
def two_adic_generator(bits: int) -> int:
    assert bits <= TWO_ADICITY, f"bits={bits} > TWO_ADICITY={TWO_ADICITY}"
    return TWO_ADIC_GENERATORS[bits]