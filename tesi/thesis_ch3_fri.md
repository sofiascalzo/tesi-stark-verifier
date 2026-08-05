# Chapter 3 — The FRI Protocol

The Fast Reed-Solomon Interactive Oracle Proof of Proximity (FRI), introduced by Ben-Sasson, Bentov, Horesh, and Riabzev~\cite{BBHR18}, is the core cryptographic component of the STARK verification system. FRI provides a mechanism for a prover to convince a verifier that a committed vector of field elements is close to the evaluation of a low-degree polynomial — a property known as *proximity to a Reed-Solomon codeword*.

This chapter presents FRI in three layers. We begin with the algebraic operation that drives the protocol — the folding of polynomials — and then describe the full protocol as an interactive oracle proof of proximity. We show how FRI can be used as a polynomial commitment scheme, connecting it to the abstract PCS interface defined in Section 2.8. We conclude with an analysis of the soundness guarantees and the concrete parameter choices used in our implementation.


## 3.1 Overview and Intuition

The central problem that FRI solves is the following: given oracle access to a function $f \colon D \to \mathbb{F}$, determine whether $f$ is (close to) the evaluation of a polynomial of degree less than $d$, where $|D|$ is much larger than $d$.

A naive approach would require the verifier to read the entire oracle (all $|D|$ values), interpolate, and check the degree — but this defeats the purpose of succinctness. FRI achieves verification in $O(\log^2 d)$ queries through a recursive strategy: at each round, the prover combines the even- and odd-degree components of the polynomial using a random challenge from the verifier, producing a new polynomial of half the degree over a domain of half the size. After $\log_2 d$ rounds, the polynomial has been reduced to a constant, which the prover sends directly. The verifier then spot-checks the consistency of each reduction step.

The key insight is that if the original function is far from any low-degree polynomial, then with high probability, at least one of the folding steps will produce an inconsistency that the verifier can detect.


## 3.2 The Folding Operation

The folding operation is the algebraic core of FRI. It reduces a polynomial of degree $d$ to a polynomial of degree $\lfloor d/2 \rfloor$ using a single random field element.

**Definition 3.1** (Even-Odd Decomposition). Let $f(X) \in \mathbb{F}[X]$ be a polynomial of degree at most $d$. The *even-odd decomposition* of $f$ is

$$f(X) = f_e(X^2) + X \cdot f_o(X^2),$$

where $f_e$ and $f_o$ are the unique polynomials satisfying

$$f_e(Y) = \sum_{i \text{ even}} c_i \, Y^{i/2}, \qquad f_o(Y) = \sum_{i \text{ odd}} c_i \, Y^{(i-1)/2}.$$

Both $f_e$ and $f_o$ have degree at most $\lfloor d/2 \rfloor$.

**Definition 3.2** (FRI Folding~\cite{BBHR18}). Given a polynomial $f(X)$ of degree at most $d$ and a random challenge $\alpha \in \mathbb{F}$, the *FRI fold* of $f$ with respect to $\alpha$ is

$$f^{(\alpha)}(Y) = f_e(Y) + \alpha \cdot f_o(Y).$$

The folded polynomial $f^{(\alpha)}$ has degree at most $\lfloor d/2 \rfloor$.

The folding can be computed directly from evaluations without access to the coefficients. If $f$ is evaluated on a domain $D$ that is closed under negation (i.e., $x \in D \implies -x \in D$), then the values of $f^{(\alpha)}$ on the *squared domain* $D^{(2)} = \{x^2 : x \in D\}$ can be computed as

$$f^{(\alpha)}(x^2) = \frac{1}{2}\left[(1 + \alpha \cdot x^{-1}) \cdot f(x) + (1 - \alpha \cdot x^{-1}) \cdot f(-x)\right].$$

This formula uses only the pair of evaluations $f(x)$ and $f(-x)$, which map to the same point $x^2$ in the squared domain. As a result, $|D^{(2)}| = |D|/2$: the domain halves at each round.

**Example.** Consider $f(X) = 1 + 2X + 3X^2 + X^3$ over $\mathbb{F}_{17}$. The even-odd decomposition gives $f_e(Y) = 1 + 3Y$ and $f_o(Y) = 2 + Y$. With challenge $\alpha = 3$:

$$f^{(3)}(Y) = (1 + 3Y) + 3(2 + Y) = 7 + 6Y.$$

The degree has been reduced from 3 to 1. A second fold with challenge $\alpha' = 5$ gives $f^{(3,5)}(Z) = 7 + 5 \cdot 6 = 37 \equiv 3 \pmod{17}$, a constant.


## 3.3 The FRI Protocol

Let $f$ be a polynomial of degree less than $d$, evaluated on a domain $D_0$ of size $n = d / \rho$, where $\rho$ is the rate (inverse of the blowup factor). The domain $D_0$ is a coset of a multiplicative subgroup of $\mathbb{F}$, chosen so that it supports recursive halving. The protocol proceeds in two phases.


### 3.3.1 Commit Phase

The commit phase produces a sequence of oracle messages (Merkle commitments) and reduces the degree of the polynomial to zero.

\begin{algorithm}
**Algorithm 1:** FRI Commit Phase

**Input:** Evaluations $u_0 = (f(x))_{x \in D_0}$, degree bound $d$, rate $\rho$

**Output:** Merkle roots $\{r_0, r_1, \ldots, r_{k-1}\}$, final constant $c$

1. Set $k = \log_2(\rho \cdot |D_0|)$ (number of folding rounds).
2. For $i = 0, 1, \ldots, k-1$:
   a. Compute the Merkle tree over $u_i$ and send the root $r_i$ to the verifier.
   b. Receive a random challenge $\alpha_i$ from the verifier.
   c. Compute $u_{i+1}$ by applying the folding operation with challenge $\alpha_i$:
      for each $x^2 \in D_{i+1}$, compute $u_{i+1}[x^2]$ from the pair $(u_i[x], u_i[-x])$.
   d. Set $D_{i+1} = D_i^{(2)}$ (the squared domain, of size $|D_i|/2$).
3. Send $c = u_k$ (a single field element) to the verifier.
\end{algorithm}

At each round, the domain halves and the degree bound halves. After $k$ rounds, the domain has size $d$ and the polynomial (if honest) has degree 0, i.e., it is a constant.

In the non-interactive setting (via the BCS transformation, Section 2.7), the challenges $\alpha_i$ are derived from the Merkle roots using the Fiat-Shamir heuristic:

$$\alpha_i = H(r_0, \alpha_0, r_1, \alpha_1, \ldots, r_i),$$

where $H$ is a cryptographic hash function modeled as a random oracle. In our implementation, this is handled by the challenger module, which follows a duplex sponge construction as described by Chiesa and Orrù~\cite{CO25}.


### 3.3.2 Query Phase

The query phase checks the consistency of the folding reductions at randomly chosen positions.

\begin{algorithm}
**Algorithm 2:** FRI Query Phase (Verifier)

**Input:** Merkle roots $\{r_0, \ldots, r_{k-1}\}$, final constant $c$, number of queries $s$

**Output:** $\mathsf{accept}$ or $\mathsf{reject}$

1. Sample $s$ random indices $\{j_1, \ldots, j_s\}$ in $\{0, \ldots, |D_0|/2 - 1\}$.
2. For each query index $j$:
   a. For each round $i = 0, 1, \ldots, k-1$:
      - Request the values $u_i[j]$ and $u_i[j + |D_i|/2]$ from the prover, together with their Merkle authentication paths.
      - Verify both Merkle paths against root $r_i$.
      - Compute the expected folded value:
        $$v = \frac{1}{2}\left[(1 + \alpha_i \cdot x_j^{-1}) \cdot u_i[j] + (1 - \alpha_i \cdot x_j^{-1}) \cdot u_i[j + |D_i|/2]\right]$$
        where $x_j$ is the domain element at index $j$ in $D_i$.
      - If $i < k-1$: verify that $v = u_{i+1}[j \bmod |D_{i+1}|]$ (checking against the next layer's commitment).
      - If $i = k-1$: verify that $v = c$ (checking against the final constant).
      - Update $j \leftarrow j \bmod |D_{i+1}|$ for the next round.
   b. If any check fails, output $\mathsf{reject}$.
3. Output $\mathsf{accept}$.
\end{algorithm}

Each query involves $O(k) = O(\log d)$ Merkle path verifications and $O(k)$ field operations. The total verifier work is $O(s \cdot \log d \cdot \log n)$, where the additional $\log n$ factor comes from the Merkle path length.


### 3.3.3 Colinearity Interpretation

The folding consistency check at each round can be equivalently understood as a **colinearity test**. Consider three points:

$$P_1 = (x, \; u_i[j]), \qquad P_2 = (-x, \; u_i[j + |D_i|/2]), \qquad P_3 = (\alpha_i, \; u_{i+1}[j']).$$

The folding formula is equivalent to requiring that $P_1$, $P_2$, and $P_3$ lie on the same line — i.e., the unique line through $(x, f(x))$ and $(-x, f(-x))$ evaluated at $\alpha_i$ gives $f^{(\alpha_i)}(x^2)$. This geometric viewpoint connects FRI to classical low-degree testing: each query checks that a local constraint (three points on a line) is satisfied, and the Proximity Gap Theorem~\cite{BCIKS20} ensures that enough such checks guarantee global proximity to a Reed-Solomon codeword.


## 3.4 FRI as a Polynomial Commitment Scheme

The FRI protocol, as described above, is an IOPP — it tests whether a committed vector is close to a low-degree polynomial. To use FRI as a polynomial commitment scheme in the sense of Definition 2.8, we need to support evaluation proofs: given a commitment to $f$ and a point $z$, prove that $f(z) = v$.

The standard technique, following the approach in Plonky2 and Plonky3, is **quotienting**. Observe that if $f(z) = v$, then the polynomial

$$q(X) = \frac{f(X) - v}{X - z}$$

is a polynomial of degree $\deg(f) - 1$. Conversely, if $f(z) \neq v$, then $q(X)$ has a pole at $z$ and is not a polynomial. Therefore, proving $f(z) = v$ reduces to proving that $q(X)$ has low degree — which is precisely what FRI does.

This gives the following PCS construction:

**$\mathsf{Commit}(f)$**: Evaluate $f$ on the domain $D_0$, build a Merkle tree over the evaluations, and output the root as the commitment $C$.

**$\mathsf{Open}(f, z, v)$**: Compute the quotient $q(X) = (f(X) - v) / (X - z)$ by evaluating it on $D_0$ (note that $z \notin D_0$ by construction), and run the FRI commit phase on $q$. The evaluation proof $\pi$ consists of the FRI proof for $q$ together with the Merkle openings of $f$ at the queried positions.

**$\mathsf{Verify}(C, z, v, \pi)$**: Run the FRI verifier on the quotient proof. At each queried position $x_j \in D_0$, reconstruct $q(x_j) = (f(x_j) - v) / (x_j - z)$ from the opened value $f(x_j)$ and verify consistency with the FRI layers. Accept if and only if all FRI checks pass.

For multi-point openings — proving $f(z_1) = v_1, \ldots, f(z_m) = v_m$ simultaneously — the quotient generalizes to

$$q(X) = \frac{f(X) - I(X)}{Z_S(X)},$$

where $S = \{z_1, \ldots, z_m\}$, $Z_S(X) = \prod_{i=1}^{m}(X - z_i)$ is the vanishing polynomial of $S$, and $I(X)$ is the unique polynomial of degree less than $m$ satisfying $I(z_i) = v_i$ for all $i$. The DEEP method (Domain Extension for Eliminating Pretenders)~\cite{BGKS20} extends this approach to sample evaluation points outside the original domain, which is necessary when the evaluation domain and the constraint domain overlap.


## 3.5 Soundness

The security of FRI rests on the following question: if the prover's initial codeword $u_0$ is $\delta$-far from every Reed-Solomon codeword (i.e., it disagrees with every polynomial of degree less than $d$ on at least a $\delta$-fraction of positions), what is the probability that the verifier accepts?


### 3.5.1 The Proximity Gap Theorem

The theoretical foundation of FRI soundness is the **Proximity Gap Theorem** of Ben-Sasson, Carmon, Ishai, Kopparty, and Saraf~\cite{BCIKS20}.

Informally, the theorem states the following. Consider a linear combination of functions $g_1, \ldots, g_t$ evaluated on a domain $D$:

$$G(X) = \sum_{i=1}^{t} \beta_i \cdot g_i(X),$$

where $\beta_1, \ldots, \beta_t$ are random field elements. If $G$ is $\delta$-close to a Reed-Solomon codeword (with $\delta$ within the unique decoding radius), then *every* $g_i$ must be $\delta'$-close to a Reed-Solomon codeword, where $\delta'$ depends on $\delta$ and the code rate.

In the context of FRI, the folding operation at each round is precisely such a random linear combination (with $t = 2$, combining $f_e$ and $f_o$). The Proximity Gap Theorem ensures that if the folded polynomial passes the low-degree test, then the original polynomial must have been close to low-degree as well. This property propagates through all folding rounds, providing soundness for the entire protocol.


### 3.5.2 Soundness Bounds

The soundness of FRI is characterized by three regimes~\cite{BBHR18, ethSTARK, BCIKS20}:

**Conjectured bound.** Under the conjecture used in the ethSTARK documentation~\cite{ethSTARK}, each query provides $\log_2(1/\rho)$ bits of security, where $\rho$ is the rate. For $s$ queries:

$$\varepsilon_{\text{FRI}} \leq \rho^s.$$

With a blowup factor of $b = 1/\rho$, this gives $s \cdot \log_2(b)$ bits of security from queries alone.

**Johnson bound.** The provable (unconditional) soundness guarantee holds when the distance $\delta$ exceeds the Johnson bound $1 - \sqrt{\rho}$. In this regime, each query provides at least $\log_2(1/\rho) / 2$ bits of security. This bound is weaker but does not rely on any unproven conjecture.

**Recent improvements.** Chai and Fan have established unconditional bounds that extend beyond the Johnson bound, partially closing the gap between the conjectured and provable regimes. These results build on the correlated agreement framework of Garreta, Mohnblatt, and Wagner.

The total security level of the FRI-based STARK system also includes **grinding** (proof-of-work): the prover must find a nonce such that the hash of the transcript has a prescribed number of leading zero bits. This adds $g$ bits of security at the cost of $2^g$ additional hash evaluations by the prover. The overall security level is:

$$\lambda \approx s \cdot \log_2(1/\rho) + g,$$

under the conjectured bound.


## 3.6 Parameter Selection

The choice of FRI parameters determines the trade-off between proof size, prover time, and security level. The following table summarizes the parameters used in our implementation, alongside the choices made by Plonky3 and ethSTARK for comparison.

| Parameter | Symbol | Our choice | Plonky3 (BabyBear) | ethSTARK |
|---|---|---|---|---|
| Field | $\mathbb{F}_p$ | BabyBear ($2^{31} - 2^{27} + 1$) | BabyBear | Goldilocks ($2^{64} - 2^{32} + 1$) |
| Extension degree | $k$ | 4 | 4 | 3 |
| Blowup factor | $1/\rho$ | 4 | 4 | 4–16 |
| Number of queries | $s$ | 50 | $\sim$33 | 12–80 |
| Grinding bits | $g$ | 16 | 16 | 20 |
| Security (conj.) | $\lambda$ | $50 \cdot 2 + 16 = 116$ | $\sim$82 + 16 = 98 | varies |

These parameters are not definitive and may be adjusted based on the advisor's requirements. The key relationship is:

$$\lambda = s \cdot \log_2(1/\rho) + g.$$

Increasing the blowup factor $1/\rho$ provides more bits per query but increases the prover's work proportionally (the evaluation domain grows). Increasing the number of queries $s$ provides more bits but increases the proof size (each query requires $O(\log n)$ Merkle authentication hashes). Grinding bits $g$ are cheap for the verifier but cost the prover $O(2^g)$ hashes.

For the BabyBear field with quartic extension, random challenges are sampled from $\mathbb{F}_{p^4}$, which has approximately $2^{124}$ elements. This ensures that the probability of a challenge collision is negligible, and the field-size-dependent terms in the soundness bound are dominated by the query-based terms.


## 3.7 Summary

The FRI protocol provides a transparent, post-quantum polynomial commitment scheme through the elegant mechanism of recursive folding. Starting from a polynomial of degree $d$ evaluated on a domain of size $d/\rho$, FRI reduces the degree by half at each round using random challenges, committing each intermediate layer with a Merkle tree. The verifier checks the consistency of these reductions at randomly chosen positions, achieving $O(s \cdot \log d \cdot \log(d/\rho))$ verification complexity with a proof of size $O(s \cdot \log^2(d/\rho))$ hash digests.

The Proximity Gap Theorem~\cite{BCIKS20} provides the theoretical backbone: it guarantees that folding preserves the proximity structure, so that a successful verification implies the original function was close to a low-degree polynomial. Combined with the BCS transformation (Section 2.7) and the quotienting technique (Section 3.4), FRI serves as the complete polynomial commitment scheme upon which the STARK construction of Chapter 4 is built.
