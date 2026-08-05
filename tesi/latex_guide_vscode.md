# LaTeX on VS Code — Guida pratica per la tesi

## È simile al Markdown?

Sì e no. L'idea è la stessa: scrivi testo con dei comandi di markup e ottieni un documento formattato. Ma LaTeX è molto più potente (e verboso).

| Cosa vuoi fare | Markdown | LaTeX |
|---|---|---|
| Grassetto | `**testo**` | `\textbf{testo}` |
| Corsivo | `*testo*` | `\textit{testo}` |
| Titolo sezione | `## Titolo` | `\section{Titolo}` |
| Sottosezione | `### Titolo` | `\subsection{Titolo}` |
| Lista puntata | `- item` | `\begin{itemize} \item ... \end{itemize}` |
| Lista numerata | `1. item` | `\begin{enumerate} \item ... \end{enumerate}` |
| Formula inline | `$E = mc^2$` | `$E = mc^2$` (uguale!) |
| Formula centrata | `$$E = mc^2$$` | `\[ E = mc^2 \]` |
| Link | `[testo](url)` | `\href{url}{testo}` |
| Immagine | `![alt](path)` | `\includegraphics{path}` |
| Citazione biblio | (non nativo) | `\cite{BBHR18}` |
| Riferimento incrociato | (non nativo) | `\ref{sec:fri}`, `\ref{thm:soundness}` |

Le differenze principali:
- LaTeX ha un **preambolo** (prima di `\begin{document}`) dove carichi i pacchetti
- Le formule funzionano quasi uguale (stessa sintassi, LaTeX è l'originale)
- LaTeX ha ambienti (`\begin{...} ... \end{...}`) per teoremi, definizioni, prove
- LaTeX gestisce la bibliografia con BibTeX — fondamentale per la tesi


---

## Setup su VS Code

### 1. Installa LaTeX

**macOS:**
```bash
brew install --cask mactex
# oppure la versione leggera:
brew install --cask basictex
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install texlive-full
# oppure la versione leggera:
sudo apt install texlive-base texlive-latex-extra texlive-bibtex-extra biber
```

**Windows:**
Scarica e installa MiKTeX da https://miktex.org/download


### 2. Installa l'estensione VS Code

Cerca e installa: **LaTeX Workshop** (di James Yu)

Questa estensione ti dà:
- Compilazione automatica quando salvi (Ctrl+S)
- Preview del PDF a fianco del codice
- Syntax highlighting
- Autocompletamento dei comandi LaTeX
- Pannello degli errori

### 3. Configurazione consigliata

Apri Settings (JSON) in VS Code (`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)") e aggiungi:

```json
{
  "latex-workshop.latex.autoBuild.run": "onSave",
  "latex-workshop.latex.recipes": [
    {
      "name": "pdflatex → bibtex → pdflatex × 2",
      "tools": ["pdflatex", "bibtex", "pdflatex", "pdflatex"]
    }
  ],
  "latex-workshop.latex.tools": [
    {
      "name": "pdflatex",
      "command": "pdflatex",
      "args": ["-synctex=1", "-interaction=nonstopmode", "%DOC%"]
    },
    {
      "name": "bibtex",
      "command": "bibtex",
      "args": ["%DOCFILE%"]
    }
  ],
  "latex-workshop.view.pdf.viewer": "tab"
}
```

Questo fa sì che ogni volta che salvi, LaTeX compila il PDF e aggiorna la preview.


---

## Struttura del file della tesi

```latex
\documentclass[12pt, a4paper]{report}   % 'report' per tesi (ha \chapter)

%%% PREAMBOLO — pacchetti %%%
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}             % tesi in inglese
\usepackage{amsmath, amssymb, amsthm}   % formule + ambienti teorema
\usepackage{mathtools}                  % estensioni di amsmath
\usepackage{hyperref}                   % link cliccabili nel PDF
\usepackage{cleveref}                   % ref intelligenti: \cref{thm:foo}
\usepackage{graphicx}                   % immagini
\usepackage{booktabs}                   % tabelle belle
\usepackage{algorithm2e}                % pseudocodice
\usepackage{listings}                   % code listings
\usepackage[backend=bibtex,             % oppure biber
            style=numeric,
            sorting=nyt]{biblatex}
\addbibresource{references.bib}         % file della bibliografia

%%% Ambienti per definizioni/teoremi %%%
\theoremstyle{definition}
\newtheorem{definition}{Definition}[chapter]   % numerazione per capitolo
\newtheorem{example}{Example}[chapter]

\theoremstyle{plain}
\newtheorem{theorem}{Theorem}[chapter]
\newtheorem{lemma}[theorem]{Lemma}             % condivide il contatore
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}

\theoremstyle{remark}
\newtheorem{remark}{Remark}[chapter]

%%% Comandi custom %%%
\newcommand{\F}{\mathbb{F}}             % campo finito
\newcommand{\Fp}{\mathbb{F}_p}          % campo primo
\newcommand{\Fpk}{\mathbb{F}_{p^4}}     % estensione quartica
\newcommand{\RS}{\mathrm{RS}}           % Reed-Solomon
\newcommand{\Commit}{\mathsf{Commit}}
\newcommand{\Open}{\mathsf{Open}}
\newcommand{\Verify}{\mathsf{Verify}}
\newcommand{\Setup}{\mathsf{Setup}}
\newcommand{\Prover}{\mathcal{P}}
\newcommand{\Verifier}{\mathcal{V}}

\begin{document}

\title{A STARK Verification System over BabyBear with FRI}
\author{Il Tuo Nome}
\date{2026}
\maketitle

\tableofcontents

\input{chapters/ch1_introduction}
\input{chapters/ch2_background}
\input{chapters/ch3_fri}
\input{chapters/ch4_stark}
\input{chapters/ch5_implementation}
\input{chapters/ch6_conclusions}

\printbibliography

\end{document}
```


---

## Come scrivere definizioni con citazioni

Questo è il punto chiave: ogni definizione formale deve avere il suo riferimento. Ecco il pattern:

```latex
\begin{definition}[Interactive Proof System {\cite[Def.~2.1]{Thaler2022}}]
\label{def:ip}
An \emph{interactive proof system} for a language $\mathcal{L}$ is a pair 
$(\Prover, \Verifier)$ where $\Prover$ is a computationally unbounded prover 
and $\Verifier$ is a probabilistic polynomial-time verifier. The protocol 
proceeds in rounds, and must satisfy:
\begin{itemize}
    \item \textbf{Completeness:} For every $x \in \mathcal{L}$,
    $\Pr[\Verifier \text{ accepts}] \geq 1 - \varepsilon_c$.
    \item \textbf{Soundness:} For every $x \notin \mathcal{L}$ and every 
    cheating prover $\Prover^*$,
    $\Pr[\Verifier \text{ accepts}] \leq \varepsilon_s$.
\end{itemize}
\end{definition}

\begin{definition}[Interactive Oracle Proof {\cite{BCS2016}}]
\label{def:iop}
An \emph{interactive oracle proof} (IOP) for a language $\mathcal{L}$ is an 
interactive protocol between a prover $\Prover$ and a verifier $\Verifier$ in 
which each prover message $\pi_i$ is an oracle that the verifier may query at 
arbitrary positions. After $k$ rounds, the verifier makes a bounded number of 
queries to $\pi_1, \ldots, \pi_k$ and outputs $\mathsf{accept}$ or 
$\mathsf{reject}$.
\end{definition}

As shown in \cref{def:iop}, the IOP model generalizes both interactive 
proofs (\cref{def:ip}) and probabilistically checkable proofs~\cite{AS1998}.
```

### Pattern delle citazioni:

```latex
% Citazione semplice
... as introduced in~\cite{BBHR18}.

% Citazione con posizione specifica (capitolo, definizione, teorema)
... following~\cite[Definition~3.1]{BCS2016}.
... as proven in~\cite[Theorem~4.2]{BCIKS20}.
... see~\cite[Chapter~4]{Thaler2022} for a comprehensive treatment.

% Citazioni multiple
... building on prior work~\cite{BBHR18, BCS2016, BCIKS20}.

% Citazione all'inizio della frase (nome visibile)
\textcite{Thaler2022} provides a comprehensive treatment of...
Ben-Sasson et al.~\cite{BBHR18} introduced the STARK construction...
```


---

## File della bibliografia (references.bib)

Crea un file `references.bib` nella stessa cartella:

```bibtex
@inproceedings{BBHR18,
  author    = {Eli Ben-Sasson and Iddo Bentov and Yinon Horesh 
               and Michael Riabzev},
  title     = {Scalable, Transparent, and Post-Quantum Secure 
               Computational Integrity},
  booktitle = {IACR Cryptology ePrint Archive},
  year      = {2018},
  note      = {Report 2018/046}
}

@inproceedings{BCS2016,
  author    = {Eli Ben-Sasson and Alessandro Chiesa and Nicholas Spooner},
  title     = {Interactive Oracle Proofs},
  booktitle = {Theory of Cryptography Conference (TCC)},
  year      = {2016},
  note      = {IACR ePrint 2016/116}
}

@inproceedings{BCIKS20,
  author    = {Eli Ben-Sasson and Dan Carmon and Yuval Ishai 
               and Swastik Kopparty and Shubhangi Saraf},
  title     = {Proximity Gaps for Reed-Solomon Codes},
  booktitle = {Proceedings of FOCS},
  year      = {2020}
}

@book{Thaler2022,
  author    = {Justin Thaler},
  title     = {Proofs, Arguments, and Zero-Knowledge},
  publisher = {Foundations and Trends in Privacy and Security},
  year      = {2022}
}

@inproceedings{KZG10,
  author    = {Aniket Kate and Gregory Zaverucha and Ian Goldberg},
  title     = {Constant-Size Commitments to Polynomials and 
               Their Applications},
  booktitle = {ASIACRYPT},
  year      = {2010}
}

@inproceedings{Groth16,
  author    = {Jens Groth},
  title     = {On the Size of Pairing-based Non-interactive Arguments},
  booktitle = {EUROCRYPT},
  year      = {2016}
}

@misc{GWC19,
  author    = {Ariel Gabizon and Zachary Williamson and Oana Ciobotaru},
  title     = {{PLONK}: Permutations over Lagrange-bases for Oecumenical 
               Noninteractive arguments of Knowledge},
  year      = {2019},
  note      = {IACR ePrint 2019/953}
}

@inproceedings{FS86,
  author    = {Amos Fiat and Adi Shamir},
  title     = {How to Prove Yourself: Practical Solutions to 
               Identification and Signature Problems},
  booktitle = {CRYPTO},
  year      = {1986}
}

@inproceedings{Merkle89,
  author    = {Ralph Merkle},
  title     = {A Certified Digital Signature},
  booktitle = {CRYPTO},
  year      = {1989}
}

@misc{CO25,
  author    = {Alessandro Chiesa and Eylon Orr\"{u}},
  title     = {Fiat-Shamir via Sponges},
  year      = {2025},
  note      = {IACR ePrint 2025/536}
}

@misc{ethSTARK,
  author    = {StarkWare},
  title     = {eth{STARK} Documentation},
  year      = {2021},
  howpublished = {\url{https://eprint.iacr.org/2021/582}}
}

@misc{GMW25,
  author    = {Gal Arnon and Giacomo Fenzi and Mathias Hall-Andersen 
               and Antonio Marcedone},
  title     = {Correlated Agreement and FRI Soundness},
  year      = {2025},
  note      = {Garreta-Mohnblatt-Wagner 2025}
}
```


---

## Workflow quotidiano

```
1.  Apri VS Code nella cartella della tesi
2.  Modifica un file .tex (es. chapters/ch2_background.tex)
3.  Salva (Ctrl+S) → LaTeX Workshop compila automaticamente
4.  Il PDF si aggiorna nel tab a destra
5.  Se ci sono errori: guarda il pannello PROBLEMS in basso
```

### Comandi utili VS Code
- `Ctrl+Alt+V` — apri preview PDF
- `Ctrl+Click` sul PDF — salta alla riga corrispondente nel .tex (SyncTeX)
- `Ctrl+Alt+J` — dal .tex salta alla posizione nel PDF


---

## Errori comuni da evitare

```latex
% ❌ SBAGLIATO: underscore senza escape nel testo
The function baby_bear_add computes...
% ✅ CORRETTO:
The function \texttt{baby\_bear\_add} computes...

% ❌ SBAGLIATO: & senza escape
P & V interact...
% ✅ CORRETTO:
$\Prover$ and $\Verifier$ interact...   % oppure P \& V

% ❌ SBAGLIATO: apici/pedici fuori da math mode
The field F_p has p elements.
% ✅ CORRETTO:
The field $\Fp$ has $p$ elements.

% ❌ SBAGLIATO: virgolette normali
He said "hello"
% ✅ CORRETTO: (backtick per aprire, apostrofo per chiudere)
He said ``hello''

% ❌ SBAGLIATO: spazi dopo i comandi
\cite{foo}e poi continuo
% ✅ CORRETTO:
\cite{foo} e poi continuo
% oppure: \cite{foo}~e poi continuo  (~ = spazio non separabile)
```


---

## Cheat sheet: dal Markdown che hai già scritto al LaTeX

Il draft che abbiamo fatto in .md si converte così:

| Nel .md | In LaTeX |
|---|---|
| `# Chapter 2 — Background` | `\chapter{Background}\label{ch:background}` |
| `## 2.1 Finite Fields` | `\section{Finite Fields}\label{sec:finite-fields}` |
| `### 2.1.1 Prime Fields` | `\subsection{Prime Fields}\label{subsec:prime-fields}` |
| `$$a^{-1} \equiv a^{p-2}$$` | `\[ a^{-1} \equiv a^{p-2} \pmod{p}. \]` |
| `**Completeness.**` | `\textbf{Completeness.}` (oppure dentro `\begin{definition}`) |
| `[BCS16]` | `\cite{BCS2016}` |
| `| col1 | col2 |` | `\begin{tabular}{ll} ... \end{tabular}` |
