# Chapter 1 — Introduction

## 1.1 Motivation

The rapid expansion of decentralized systems and blockchain technology has brought computational integrity to the forefront of modern cryptography. In these settings, a central question arises: how can one party convince another that a computation was performed correctly, without requiring the verifier to re-execute it? Zero-knowledge proof systems provide an answer by allowing a prover to convince a verifier of the validity of a statement while revealing no information beyond the truth of the statement itself.

Among the various families of proof systems developed over the past two decades, STARKs (Scalable Transparent ARguments of Knowledge) have emerged as a particularly compelling construction. Introduced by Ben-Sasson, Bentov, Horesh, and Riabzev [BBHR18], STARKs achieve several desirable properties simultaneously: transparency (no trusted setup is required), scalability (the prover runs in quasi-linear time and the verifier in polylogarithmic time), and post-quantum security (the only cryptographic assumption is the collision resistance of hash functions).

These properties make STARKs especially well-suited for blockchain scalability solutions, where thousands of off-chain transactions can be bundled into a single proof that is verified on-chain at a fraction of the original computational cost. Systems such as StarkNet, Polygon zkEVM, and SP1 rely on STARK-based proving infrastructure to process millions of transactions while inheriting the security guarantees of the underlying layer-1 blockchain.


## 1.2 Context and Related Work

The landscape of zero-knowledge proof systems is broad. On one end, SNARKs based on bilinear pairings — such as Groth16 [Gro16] and the PLONK protocol [GWC19] — offer extremely compact proofs (a few hundred bytes) and fast verification, but require either a per-circuit trusted setup (Groth16) or a universal trusted setup (PLONK with KZG commitments). These systems rely on the hardness of the discrete logarithm problem over elliptic curve groups, making them vulnerable to quantum attacks.

On the other end, STARKs trade slightly larger proof sizes for transparency and quantum resistance. The core machinery of STARKs consists of two layers: an algebraic intermediate representation (AIR) that encodes the computation as polynomial constraints over an execution trace, and a polynomial commitment scheme based on the FRI (Fast Reed-Solomon Interactive Oracle Proof of Proximity) protocol [BBHR18, BCIKS20], which enables efficient low-degree testing without relying on elliptic curves.

Two influential proving systems serve as direct references for this work:

**Halo2.** Originally developed by the Electric Coin Company for Zcash and subsequently forked by Privacy and Scaling Explorations (PSE), Halo2 implements a PLONKish arithmetization with custom gates, lookup arguments, and a permutation argument. The PSE fork replaces the original IPA-based polynomial commitment scheme with KZG over the BN254 curve, enabling cost-effective verification on Ethereum. Halo2's frontend — with its structured approach to circuit definition through regions, columns, and chips — provides a clean separation between the description of constraints and the cryptographic backend.

**Plonky2.** Developed by Polygon Zero, Plonky2 combines PLONKish arithmetization with FRI-based polynomial commitments over the Goldilocks field ($p = 2^{64} - 2^{32} + 1$). This hybrid approach eliminates the need for a trusted setup while preserving the expressiveness of custom gates and lookup arguments. Plonky2 was specifically designed for recursive proof composition, a critical feature for zkVM and rollup applications.

The more recent **Plonky3** toolkit generalizes this approach further, shifting to smaller 31-bit fields (BabyBear, KoalaBear, Mersenne-31) and an AIR-based paradigm with modular, interchangeable components. Plonky3 serves as the backend for a new generation of zkVMs including SP1 and Valida.


## 1.3 Contribution

This thesis presents the design and implementation of a STARK verification system built from first principles. The system operates over the BabyBear prime field ($p = 2^{31} - 2^{27} + 1$) and uses FRI as the polynomial commitment scheme, an approach inspired by Plonky2. The architecture integrates and adapts ideas from both Halo2 (structured constraint system, modular frontend) and Plonky2 (FRI-based commitment, small-field arithmetic).

The main contributions are:

1. **A modular, pedagogically transparent implementation** of the full STARK pipeline — from finite field arithmetic and polynomial operations, through FRI commitment and low-degree testing, to AIR-based constraint encoding and proof generation/verification — with each component designed as an independent, testable module.

2. **A detailed exposition of the underlying theory**, connecting the formal definitions of interactive oracle proofs, polynomial commitment schemes, and the BCS transformation [BCS16] to the concrete code that implements them, bridging the gap between the cryptographic literature and practical system building.

3. **An analysis of parameter selection and security**, including the soundness of the FRI protocol under both conjectured and provable bounds, the choice of blowup factor, number of queries, and grinding bits, and their impact on proof size and verification time.

The system is not intended as a production-ready prover competing with Stone, S-two, or Plonky3 on performance. Rather, it is designed to be a self-contained, readable reference implementation that demonstrates how the theoretical components of a STARK system fit together, serving as both a learning tool and a basis for further experimentation.


## 1.4 Thesis Structure

The remainder of this thesis is organized as follows.

**Chapter 2** introduces the mathematical and cryptographic background required throughout: finite fields and their extensions, polynomial arithmetic, Merkle trees, and the formal definitions of proof systems, interactive oracle proofs, and polynomial commitment schemes.

**Chapter 3** presents the FRI protocol in detail, including the commit phase, query phase, folding mechanism, and soundness analysis. The connection between FRI and the broader framework of polynomial commitment schemes is made explicit.

**Chapter 4** describes the STARK construction: the algebraic intermediate representation (AIR), execution traces, boundary and transition constraints, quotient polynomials, and the complete prover/verifier protocol. The BCS transformation that compiles the interactive protocol into a non-interactive proof is also discussed.

**Chapter 5** details the implementation: the architecture of the codebase, design decisions, testing methodology, and experimental results including proof sizes and timing measurements.

**Chapter 6** concludes the thesis with a summary of contributions and directions for future work.


---


# Chapter 2 — Background

This chapter introduces the mathematical foundations and cryptographic primitives upon which the STARK verification system is built. We begin with finite field arithmetic, proceed to polynomial representations and Merkle tree commitments, and then develop the formal framework of proof systems — from classical interactive proofs to the modern notion of interactive oracle proofs — culminating in the definition of polynomial commitment schemes and the FRI protocol.


## 2.1 Finite Fields

### 2.1.1 Prime Fields

A **prime field** $\mathbb{F}_p$ is the set of integers $\{0, 1, \ldots, p-1\}$ equipped with addition and multiplication modulo a prime $p$. The field $\mathbb{F}_p$ satisfies all the axioms of a field: closure, associativity, commutativity, the existence of additive and multiplicative identities ($0$ and $1$, respectively), additive inverses for all elements, and multiplicative inverses for all nonzero elements.

The multiplicative group $\mathbb{F}_p^*= \mathbb{F}_p \setminus \{0\}$ is cyclic of order $p - 1$. An element $g \in \mathbb{F}_p^*$ is a **generator** (or primitive root) if $\{g^0, g^1, \ldots, g^{p-2}\} = \mathbb{F}_p^*$. Multiplicative inverses can be computed via Fermat's little theorem: for any $a \in \mathbb{F}_p^*$,

$$a^{-1} \equiv a^{p-2} \pmod{p}.$$


### 2.1.2 The BabyBear Field

The system implemented in this thesis operates over the **BabyBear** prime field, defined by

$$p = 2^{31} - 2^{27} + 1 = 2013265921.$$

This prime is specifically chosen for its favorable computational properties:

**Efficient arithmetic.** Since $p < 2^{31}$, every field element fits in a 32-bit unsigned integer. Products of two elements fit in a 64-bit integer, and the modular reduction $a \bmod p$ can be performed using the identity $2^{31} \equiv 2^{27} - 1 \pmod{p}$, which avoids expensive division instructions.

**High 2-adicity.** The multiplicative group $\mathbb{F}_p^*$ has order $p - 1 = 2^{27} \cdot 15$. The factor $2^{27}$ means that $\mathbb{F}_p^*$ contains a cyclic subgroup of order $2^{27}$, which is essential for performing the Number Theoretic Transform (NTT) — the finite field analogue of the Fast Fourier Transform. The NTT enables polynomial multiplication and evaluation in $O(n \log n)$ time, and is the computational backbone of both the FRI protocol and the STARK prover.

Concretely, let $\omega \in \mathbb{F}_p$ be a primitive $2^{27}$-th root of unity, i.e., an element satisfying $\omega^{2^{27}} = 1$ and $\omega^{2^{27}/2} \neq 1$. Then the set

$$H = \{1, \omega, \omega^2, \ldots, \omega^{2^{27}-1}\}$$

is a multiplicative subgroup of order $2^{27}$. Any subgroup of order $2^k$ for $k \leq 27$ can be obtained by taking an appropriate power of $\omega$: the element $\omega^{2^{27-k}}$ generates a subgroup of order $2^k$.


### 2.1.3 Field Extensions

For certain operations in the STARK protocol — particularly the sampling of random challenges in the FRI folding phase — it is necessary to work over a larger field to ensure adequate soundness. The base field $\mathbb{F}_p$ has approximately $2^{31}$ elements, which provides at most 31 bits of security per random challenge. To achieve the standard security level of 128 bits, we extend the field.

A **field extension** $\mathbb{F}_{p^k}$ of degree $k$ over $\mathbb{F}_p$ is constructed as the quotient ring $\mathbb{F}_p[X] / (f(X))$, where $f(X) \in \mathbb{F}_p[X]$ is an irreducible polynomial of degree $k$. Elements of $\mathbb{F}_{p^k}$ are represented as polynomials of degree less than $k$ with coefficients in $\mathbb{F}_p$:

$$\mathbb{F}_{p^k} = \{a_0 + a_1\alpha + a_2\alpha^2 + \cdots + a_{k-1}\alpha^{k-1} : a_i \in \mathbb{F}_p\},$$

where $\alpha$ is a root of $f(X)$.

In this work, we use the **quartic extension** $\mathbb{F}_{p^4}$, which provides a field of approximately $2^{124}$ elements — sufficient for 124-bit soundness per challenge. Each element of $\mathbb{F}_{p^4}$ is represented as a tuple $(a_0, a_1, a_2, a_3) \in \mathbb{F}_p^4$, corresponding to $a_0 + a_1\alpha + a_2\alpha^2 + a_3\alpha^3$. Addition is componentwise; multiplication requires reducing modulo the irreducible polynomial, which introduces cross-terms that depend on the specific choice of $f(X)$.


## 2.2 Polynomials

### 2.2.1 Representation and Evaluation

A univariate polynomial over $\mathbb{F}_p$ of degree at most $d$ is an element of the ring $\mathbb{F}_p[X]$:

$$f(X) = \sum_{i=0}^{d} c_i X^i, \quad c_i \in \mathbb{F}_p.$$

The **coefficient representation** stores $f$ as the vector $(c_0, c_1, \ldots, c_d)$. The **evaluation representation** stores $f$ as its values on a fixed domain $D = \{x_0, x_1, \ldots, x_n\}$, i.e., as the vector $(f(x_0), f(x_1), \ldots, f(x_n))$.

Given $n+1$ distinct evaluation points, the polynomial of degree at most $n$ passing through them is unique and can be recovered via **Lagrange interpolation**:

$$f(X) = \sum_{i=0}^{n} f(x_i) \prod_{\substack{j=0 \\ j \neq i}}^{n} \frac{X - x_j}{x_i - x_j}.$$


### 2.2.2 The Number Theoretic Transform

When the evaluation domain $D$ is a multiplicative subgroup of $\mathbb{F}_p$ — say $D = \{1, \omega, \omega^2, \ldots, \omega^{N-1}\}$ where $\omega$ is a primitive $N$-th root of unity and $N$ is a power of 2 — the conversion between coefficient and evaluation representations can be performed in $O(N \log N)$ operations using the **Number Theoretic Transform (NTT)**, the finite-field analogue of the FFT.

The NTT computes:

$$\hat{f}_k = \sum_{j=0}^{N-1} c_j \cdot \omega^{jk}, \quad k = 0, 1, \ldots, N-1,$$

which is precisely the evaluation $f(\omega^k)$. The inverse NTT recovers the coefficients:

$$c_j = N^{-1} \sum_{k=0}^{N-1} \hat{f}_k \cdot \omega^{-jk}.$$

The divide-and-conquer structure of the NTT — splitting even and odd coefficients and recursing on subgroups of half the size — relies on the 2-adic structure of $\mathbb{F}_p^*$. This is precisely why the BabyBear prime, with its factor of $2^{27}$ in $p-1$, is an ideal choice: it supports NTTs on domains of up to $2^{27}$ elements.


### 2.2.3 Vanishing Polynomials

Given a multiplicative subgroup $H = \{\omega^0, \omega^1, \ldots, \omega^{N-1}\}$, the **vanishing polynomial** (or zerofier) of $H$ is

$$Z_H(X) = X^N - 1 = \prod_{i=0}^{N-1}(X - \omega^i).$$

This polynomial vanishes on every element of $H$ and nowhere else. Vanishing polynomials play a fundamental role in STARKs: if a polynomial $f(X)$ is zero on $H$, then $Z_H(X)$ divides $f(X)$, and the quotient $f(X)/Z_H(X)$ is again a polynomial. Conversely, if $f(X)/Z_H(X)$ is a polynomial (rather than a rational function), this certifies that $f$ vanishes on $H$.


## 2.3 Reed-Solomon Codes

Let $\mathbb{F}$ be a finite field, $D \subseteq \mathbb{F}$ a subset of size $n$, and $d < n$ a positive integer. The **Reed-Solomon code** of degree $d$ over the evaluation domain $D$ is

$$\mathrm{RS}[D, d] = \{(f(x))_{x \in D} : f \in \mathbb{F}[X], \deg(f) < d\}.$$

Each codeword is the evaluation of a polynomial of degree less than $d$ on all points of $D$. The code has dimension $d$ (there are $d$ free coefficients) and minimum distance $n - d + 1$ (by the Schwartz-Zippel lemma, two distinct polynomials of degree less than $d$ agree on at most $d - 1$ points).

The **rate** of the code is $\rho = d/n$. In the STARK setting, $n$ is typically a multiple of $d$: if $d$ is the degree bound of the polynomial being committed to and $n = d / \rho$ is the evaluation domain size, then $\rho$ is the inverse of the **blowup factor**. For instance, a blowup factor of 4 gives $\rho = 1/4$, meaning the evaluation domain is 4 times larger than the number of coefficients.

The parameter $\rho$ controls the fundamental trade-off in FRI: smaller $\rho$ (larger blowup) provides stronger soundness per query but increases the prover's work and the proof size.


## 2.4 Merkle Trees

A **Merkle tree** [Mer89] is a binary hash tree that provides a binding commitment to an ordered sequence of values. Given a sequence $(v_0, v_1, \ldots, v_{N-1})$ with $N = 2^k$, the Merkle tree is constructed as follows:

1. Each leaf node stores the hash of a data element: $\ell_i = H(v_i)$.
2. Each internal node stores the hash of the concatenation of its children: $n = H(n_{\mathrm{left}} \| n_{\mathrm{right}})$.
3. The **root** of the tree is a single hash digest that serves as a succinct commitment to the entire sequence.

To prove that $v_i$ is the element at position $i$, the prover provides an **authentication path** (or Merkle proof): the sequence of sibling hashes along the path from the leaf $\ell_i$ to the root. The verifier recomputes the root using $v_i$ and the authentication path and checks that it matches the committed root. The authentication path has length $k = \log_2(N)$, so verification requires only $O(\log N)$ hash evaluations.

In the STARK setting, Merkle trees are used to commit to the evaluations of polynomials. The prover evaluates a polynomial $f$ on a domain $D$ of size $N$, builds a Merkle tree over the vector $(f(x))_{x \in D}$, and sends the root to the verifier. Later, the verifier can request the opening of $f$ at specific positions, and the prover responds with the value and its authentication path.


## 2.5 Proofs and Arguments

We now establish the formal framework of proof systems, following the treatment in Thaler [Tha22] and Ben-Sasson, Chiesa, and Spooner [BCS16].


### 2.5.1 Interactive Proofs

An **interactive proof system** for a language $\mathcal{L}$ is a protocol between a computationally unbounded prover $P$ and a probabilistic polynomial-time verifier $V$. The protocol proceeds in rounds: in each round, $V$ sends a message (typically a random challenge) and $P$ responds. At the end, $V$ outputs $\mathsf{accept}$ or $\mathsf{reject}$.

The system must satisfy two properties:

**Completeness.** For every $x \in \mathcal{L}$, the honest prover $P$ convinces $V$ to accept with high probability:

$$\Pr[V \text{ accepts after interacting with } P \text{ on input } x] \geq 1 - \varepsilon_c,$$

where $\varepsilon_c$ is the completeness error (typically 0 for perfect completeness).

**Soundness.** For every $x \notin \mathcal{L}$ and every (possibly cheating) prover $P^*$,

$$\Pr[V \text{ accepts after interacting with } P^* \text{ on input } x] \leq \varepsilon_s,$$

where $\varepsilon_s$ is the soundness error.


### 2.5.2 Arguments

An **argument system** relaxes the soundness condition to hold only against computationally bounded provers. That is, soundness is guaranteed against any probabilistic polynomial-time prover $P^*$, rather than against arbitrary provers. This weaker requirement often enables significantly shorter proofs.

An **argument of knowledge** additionally requires the existence of an efficient extractor $E$ such that: whenever a prover $P^*$ convinces $V$ to accept, $E$ can extract a valid witness $w$ (by rewinding or otherwise interacting with $P^*$). This notion is captured by the **knowledge soundness** property.


### 2.5.3 Non-Interactive Proofs

A **non-interactive** proof (or argument) consists of a single message from the prover to the verifier. The classical technique for removing interaction is the **Fiat-Shamir transformation** [FS86]: the verifier's random challenges are replaced by the output of a cryptographic hash function applied to the protocol transcript accumulated so far. Under the random oracle model, this transformation preserves soundness.


## 2.6 Interactive Oracle Proofs

The concept of an **Interactive Oracle Proof (IOP)**, introduced by Ben-Sasson, Chiesa, and Spooner [BCS16] and independently by Reingold, Rothblum, and Rothblum [RRR16], provides a unifying abstraction that generalizes both interactive proofs and probabilistically checkable proofs (PCPs).

**Definition (Interactive Oracle Proof).** An IOP for a language $\mathcal{L}$ is an interactive protocol between a prover $P$ and a verifier $V$ that proceeds in rounds. In each round:
1. The prover sends an oracle message $\pi_i$ (a function that the verifier can query at arbitrary points).
2. The verifier sends a random challenge $r_i$.

After $k$ rounds, the verifier makes a bounded number of queries to the oracle messages $\pi_1, \ldots, \pi_k$ and decides whether to accept or reject.

The key distinction from a standard interactive proof is that the verifier has **oracle access** to the prover's messages: rather than reading them in full, it can query them at specific positions. This query model is what enables succinctness — the verifier reads only a small fraction of the prover's messages.

An IOP of **proximity** (IOPP) is an IOP in which the verifier tests whether the prover's initial message is close to a codeword of a specified error-correcting code (typically a Reed-Solomon code), rather than testing membership in a language.


## 2.7 The BCS Transformation

The **BCS transformation** [BCS16] is a compiler that converts a public-coin IOP into a non-interactive argument in the random oracle model. The construction proceeds as follows:

1. **Commitment.** Each oracle message $\pi_i$ sent by the prover is committed using a Merkle tree. The prover sends the Merkle root $r_i$ to the verifier.

2. **Challenge derivation.** The verifier's random challenges are derived via the Fiat-Shamir heuristic: the challenge $\alpha_i$ at round $i$ is computed as $\alpha_i = H(r_1, \alpha_1, r_2, \alpha_2, \ldots, r_i)$, where $H$ is a cryptographic hash function modeled as a random oracle.

3. **Query answering.** After all rounds, the verifier determines which positions of the oracle messages it needs to query. The prover provides the values at those positions together with their Merkle authentication paths.

4. **Verification.** The verifier checks all Merkle paths against the committed roots, recomputes the challenges from the transcript, and runs the IOP verifier's decision procedure on the queried values.

The BCS transformation preserves the completeness and soundness of the underlying IOP (up to negligible loss), provided the hash function behaves as a random oracle. The resulting non-interactive proof consists of the sequence of Merkle roots, the queried values, and the authentication paths.

This is precisely the compilation strategy used in STARK systems: the IOP layer defines the algebraic protocol (AIR constraints, quotient polynomials, FRI folding), and the BCS transformation compiles it into a concrete, non-interactive proof using Merkle commitments and Fiat-Shamir challenges.


## 2.8 Polynomial Commitment Schemes

A **Polynomial Commitment Scheme (PCS)** is a cryptographic primitive that allows a prover to commit to a polynomial and later prove evaluations of that polynomial at points chosen by the verifier. Formally, a PCS consists of four algorithms:

1. $\mathsf{Setup}(\lambda, d) \to \mathsf{pp}$: generates public parameters for polynomials of degree at most $d$ at security level $\lambda$.
2. $\mathsf{Commit}(\mathsf{pp}, f) \to C$: produces a commitment $C$ to the polynomial $f$.
3. $\mathsf{Open}(\mathsf{pp}, f, z) \to (v, \pi)$: produces a proof $\pi$ that $f(z) = v$.
4. $\mathsf{Verify}(\mathsf{pp}, C, z, v, \pi) \to \{0, 1\}$: checks the proof.

The scheme must satisfy:

**Correctness.** For honestly generated commitments and proofs, the verifier always accepts.

**Binding.** A computationally bounded prover cannot open the same commitment to two different polynomials (or to two different values at the same point).

Different proof systems use different PCS constructions:

- **KZG** [KZG10] uses bilinear pairings on elliptic curves to commit to polynomials with constant-size commitments and proofs. It requires a trusted setup (a structured reference string) and is not post-quantum secure.

- **FRI-based PCS** uses the FRI protocol to commit to polynomials via Merkle trees and prove evaluations through low-degree testing. It requires no trusted setup (transparent) and relies only on hash functions (post-quantum secure). The proof size is $O(\log^2 d)$ hash digests.

The system implemented in this thesis uses a FRI-based PCS, which we describe in detail in Chapter 3.


## 2.9 Summary

The table below summarizes the cryptographic building blocks and their role in the STARK pipeline.

| Component | Role in the system |
|---|---|
| BabyBear field $\mathbb{F}_p$ | Base arithmetic for all computations |
| Quartic extension $\mathbb{F}_{p^4}$ | Domain for random challenges (128-bit soundness) |
| NTT | Efficient polynomial evaluation and interpolation |
| Vanishing polynomials | Encoding constraint satisfaction as divisibility |
| Reed-Solomon codes | Error-correcting structure tested by FRI |
| Merkle trees | Succinct commitment to polynomial evaluations |
| Interactive Oracle Proofs | Abstract protocol framework |
| BCS transformation | Compiler from IOP to non-interactive proof |
| Polynomial Commitment Scheme | Interface between IOP layer and FRI |

Chapter 3 builds on these foundations to present the FRI protocol — the concrete PCS at the heart of the STARK verifier.


---


## References

[BBHR18] E. Ben-Sasson, I. Bentov, Y. Horesh, M. Riabzev. "Scalable, transparent, and post-quantum secure computational integrity." *IACR Cryptology ePrint Archive*, 2018/046.

[BCS16] E. Ben-Sasson, A. Chiesa, N. Spooner. "Interactive Oracle Proofs." In *Theory of Cryptography Conference (TCC)*, 2016. IACR ePrint 2016/116.

[BCIKS20] E. Ben-Sasson, D. Carmon, Y. Ishai, S. Kopparty, S. Saraf. "Proximity Gaps for Reed-Solomon Codes." In *FOCS*, 2020.

[FS86] A. Fiat, A. Shamir. "How to Prove Yourself: Practical Solutions to Identification and Signature Problems." In *CRYPTO*, 1986.

[Gro16] J. Groth. "On the Size of Pairing-based Non-interactive Arguments." In *EUROCRYPT*, 2016.

[GWC19] A. Gabizon, Z. Williamson, O. Ciobotaru. "PLONK: Permutations over Lagrange-bases for Oecumenical Noninteractive arguments of Knowledge." *IACR ePrint* 2019/953.

[KZG10] A. Kate, G. Zaverucha, I. Goldberg. "Constant-Size Commitments to Polynomials and Their Applications." In *ASIACRYPT*, 2010.

[Mer89] R. Merkle. "A Certified Digital Signature." In *CRYPTO*, 1989.

[RRR16] O. Reingold, R. Rothblum, G. Rothblum. "Constant-Round Interactive Proofs for Delegating Computation." In *STOC*, 2016.

[Tha22] J. Thaler. *Proofs, Arguments, and Zero-Knowledge.* Foundations and Trends in Privacy and Security, 2022.

[CO25] A. Chiesa, E. Orrù. "Fiat-Shamir via Sponges." *IACR ePrint* 2025/536.
