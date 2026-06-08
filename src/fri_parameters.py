
# In Plonky3:
#   pub struct FriParameters<M> {
#       pub log_blowup: usize,
#       pub num_queries: usize,
#       pub proof_of_work_bits: usize,
#       pub mmcs: M,
#   }
#


from challenger import Challenger



class FriParameters:

    # blowup. 1 -> blowup 2x, rho=1/2.
    log_blowup: int
    num_queries: int
    #PoW 0 = nessun PoW.
    proof_of_work_bits: int

    def __init__(self, log_blowup: int, num_queries: int, proof_of_work_bits: int, final_poly_len: int = 2):
        self.log_blowup = log_blowup
        self.num_queries = num_queries
        self.proof_of_work_bits = proof_of_work_bits
        self.final_poly_len = final_poly_len

    def blowup(self) -> int:
        return 1 << self.log_blowup

    def observe_into(self, challenger: Challenger) -> None:

        challenger.observe_bytes(self.log_blowup.to_bytes(4, 'little'))
        challenger.observe_bytes(self.num_queries.to_bytes(4, 'little'))
        challenger.observe_bytes(self.proof_of_work_bits.to_bytes(4, 'little'))
        challenger.observe_bytes(self.final_poly_len.to_bytes(4, 'little'))