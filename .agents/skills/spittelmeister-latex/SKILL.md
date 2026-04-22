# Spittelmeister LaTeX Reports Skill — v2

Operational guidance for implementing, refactoring, or debugging **Spittelmeister**
engineering reports in a **Python + Streamlit + LaTeX** stack.

This skill is optimized for:

- modular standalone reports and combined standard reports
- compatibility with normal `pdflatex` and portable MiKTeX on Windows
- integration with Streamlit pages, session state, and YAML project persistence
- asset and figure generation from Python
- prevention of common LaTeX automation failures
- honest reporting of scope and verification limits

---

## 1. Purpose

This skill exists to help agents and developers build report pipelines that are not only
able to compile, but are also:

- structurally consistent with the **sample report**
- maintainable by module
- honest about the actual scope of implemented checks
- robust under `pdflatex` in corporate Windows environments
- integrable with Streamlit, `.tex/.pdf/.zip` export, and project persistence

The goal is not "make it compile somehow."
The goal is a trustworthy, maintainable reporting system.

---

## 2. Source of truth

When working on the standard combined report style, use this as the primary reference:

```text
examples/sample_report/main.tex
```

And, when present:

```text
examples/sample_report/report_assets/
```

Do not use old external ZIP exports as the main visual or structural reference once
the sample report has been incorporated into the repository.

---

## 3. Expected architecture

Typical repository pattern:

```text
app.py
pages/
  01_*.py ...
  04_Protokoll.py
  08_Stuetzenfuss_Hilti.py
  09_Isokorb.py
engine/
  nachweis_*.py
  *_assessment.py
  rfem/
latex/
  base.py
  protokoll_*.py
  report_combined.py
  report_bundle.py
  report_selection.py
  report_figures.py
projectio/
  mapper.py
ui/
  session.py
examples/sample_report/
```

### Responsibility split

**engine/**
- calculation logic
- input/output dataclasses
- structured assessment/results
- do not bury heavy LaTeX markup here

**latex/**
- LaTeX rendering
- macros, preambles, and visual blocks
- per-module standalone reports
- combined standard report

**pages/**
- Streamlit input capture
- engine execution
- lightweight visual summary
- save/load from session state
- standalone and combined export

**projectio/**
- YAML persistence of the project
- module serialization/deserialization

**ui/session.py**
- save/load helpers per module
- no heavy business logic here

---

## 4. Report design philosophy

### 4.1 Modular, but coherent

The standard report must achieve both:

- each module can live independently
- the combined report reads like one document

Recommended pattern for each technical module:

- first subsection: **System und Eingangswerte**
- last subsection: **Zusammenfassende Bewertung**
- when applicable, a final or penultimate subsection for:
  - **Abgrenzung**
  - open points
  - partial verification limits
  - manual follow-up required

### 4.3 Every equation block must have a symbol legend

Any equation block with 3 or more distinct symbols must be followed immediately by a
symbol legend rendered with `_sym_legend()` from `latex/base.py`.

This is not optional. Prüfingenieure and reviewers must be able to read the calculation
without consulting external references. A bare equation block is incomplete.

**What counts as an equation block:**
- `\begin{align*}...\end{align*}`
- `\[...\]` display math with 3+ symbols
- A sequence of `align*` blocks for the same calculation step

**What does not need a legend:**
- Single inline expressions like `$\eta = 0{,}83 \leq 1{,}0$`
- Trivial unit conversions
- Equations where every symbol is already defined in the preceding text

**Content of the legend:**
- Include every symbol that is not immediately obvious to a structural engineer
- Include subscripted variants: `N_{Ed}` and `N_{b,Rd}` are separate entries
- Use German descriptions — this is a German engineering report
- Use SI-compatible units; use `{-}` for dimensionless quantities

**Placement:**
Place the legend immediately after `\end{align*}` or `\]`, before the next
`\resultbox`, `\vspace`, or subsection heading.

**Example:**
```python
# After the equation block in the rf-string:
{_sym_legend([
    (r'\eta',       'Ausnutzungsgrad',                '{-}'),
    (r'N_{Ed}',      'Bemessungsnormalkraft',           'kN'),
    (r'N_{b,Rd}',    'Bemessungswert der Knicklast',    'kN'),
    (r'M_{Ed}',      'Bemessungsmoment',                'kNcm'),
    (r'M_{Rd}',      'Bemessungsmoment Widerstand',     'kNcm'),
    (r'k_{yy}',      'Interaktionsbeiwert',             '{-}'),
])}
```

See §25.9 for the full API and §8.7 for the column layout rule (always 2 per row).

### 4.2 Never invent a verification

If the engine does not yet support a real verification:

- do not fake completeness
- do not inject invented numerical results
- render the limitations explicitly:
  - limited scope
  - manual input still required
  - open points
  - dependency on manufacturer data / RFEM / Hilti / Schöck / etc.

In Spittelmeister reports, user trust is more valuable than a false feeling of
completeness.

---

## 5. Two preamble styles

Keep two clearly separated modes.

### A. Standalone / app-style

More expressive. May continue using existing green/red semantics.

### B. Combined standard report

More neutral. Closer to a formal **Prüfbericht**.

The neutral preamble variant must provide:

- `\OK`, `\IO`, `\NIO`, `\FAIL`
- `\IOstatus`, `\NIOstatus`, `\HINWEISstatus`
- `\okbox{...}`, `\failbox{...}` — using `\colorbox + \parbox`, not tcolorbox
- `\resultbox{Title}{Text}` — using tcolorbox as an environment, not inside a macro

### Rule

- **standalone** may keep legacy visual semantics
- **combined report** must explicitly request the neutral variant via a style parameter
  (e.g. `report_style="combined"` or `build_preamble(..., style="combined")`)

Do not accidentally mix both modes.

---

## 6. Recommended LaTeX grammar

### 6.1 Sectioning

For a combined report aligned with the sample report:

- use `\section{...}` and `\subsection{...}`
- avoid manual numbering such as `\subsection*{1. ...}`
- add `\needspace{...}` before important subsections

### 6.2 Typical block names

- `mandateblock`
- `scopeblock`
- `executionblock`
- `verificationmodule`
- `resultbox`
- `conclusionblock`

### 6.3 Rule for new environments

Whenever defining a `\newenvironment`, use the correct two-part form:

```latex
\newenvironment{name}{%
  <begin code>
}{%
  <end code>
}
```

Do not place `\end{tabularx}` or `\end{tcolorbox}` inside the **opening** block
(the first argument). They must be in the **closing** block (the second argument).

### 6.4 Unsafe tabularx wrapper pattern

Do not split `tabularx` across a `\newenvironment` boundary in this codebase.
Even when the syntax looks structurally correct, this pattern has repeatedly caused
runaway and body-scanning failures in real reports. Do not assume "this time it is
fine" — the failures are document-size dependent and may not appear on short tests.

That pattern causes:

- `Runaway argument`
- `\TX@get@body`
- `File ended while scanning ...`

Preferred alternative: write `tabularx` directly in the generated LaTeX body.

### 6.5 No `breakable` tcolorbox inside `\newcommand` — CRITICAL

**Do not** define macros such as `\okbox` or `\failbox` using a `\newcommand` that
internally opens a `tcolorbox` with `breakable`.

**Unsafe pattern:**

```latex
\newcommand{\okbox}[1]{%
  \begin{tcolorbox}[enhanced, breakable,...]
  \centering\textbf{#1}
  \end{tcolorbox}}
```

**Why this fails:**

`tcolorbox` with `breakable` uses `\TX@get@body` to scan its body in the token stream.
Inside `\newcommand`, the argument `#1` is already substituted before `tcolorbox` can
safely scan it, breaking the scanning mechanism.

This produces:

```
! File ended while scanning use of \TX@get@body.
```

**This failure is document-size dependent.** A short test document may compile without
errors, while the same definition causes a fatal crash at the end of a long report
(26+ pages). Do not validate the fix on a short test case alone.

**Safe alternatives:**

For small one-shot result boxes:

```latex
\newcommand{\okbox}[1]{%
  \par\vspace{8pt}\noindent
  \colorbox{SPLightGray}{\parbox{\dimexpr\linewidth-2\fboxsep}{%
    \centering\textbf{#1}}}\par\vspace{8pt}}
```

For long body-capturing blocks: use a real `\newenvironment` or `\NewEnviron` (see 6.6).

### 6.6 Body-capturing environments with `\NewEnviron`

When a block needs to capture a long body and pass it to tcolorbox or tabularx, use
the `environ` package pattern:

```latex
\NewEnviron{myblock}{%
  \begin{tcolorbox}[...]
  \BODY
  \end{tcolorbox}
}
```

**Before using `\NewEnviron`:** verify that the `environ` package is already in the
project preamble or has been centrally approved per the package governance rule (§13).
Do not add it ad hoc inside module renderers.

### 6.7 Symbol legend placement rule

After every non-trivial equation block, add a symbol legend using `_sym_legend()`
from `latex/base.py`. See §4.3 for the content rules and §8.7 for the layout rules.

The call belongs **inside the rf-string** of the module body, immediately after
`\end{align*}`:

```python
return rf"""
...
\begin{{align*}}
\eta &= \frac{{N_{{ed}}}}{{N_{{b,Rd}}}} + k_{{yy}}\,\frac{{M_{{ed}}}}{{M_{{Rd}}}}
     = {r.eta:.4f}
\end{{align*}}

{interaction_legend_tex}

\vspace{{10pt}}
{result_box}
"""
```

Where `interaction_legend_tex` was built earlier in `_body_content()`:

```python
interaction_legend_tex = _sym_legend([
    (r'\eta',    'Ausnutzungsgrad',             '{-}'),
    (r'N_{ed}',   'Bemessungsnormalkraft',        'kN'),
    (r'N_{b,Rd}', 'Bemessungswert der Knicklast', 'kN'),
    ...
])
```

Build all legends at the top of `_body_content()`, before the rf-string. This keeps
the rf-string readable and the legend definitions close to each other.

Do not hardcode the tabular spec — always use `_sym_legend()`. A handwritten tabular
may silently use 3 columns and overflow A4 (see §8.7).

---

## 7. Hard rules for Python-generated LaTeX

### 7.1 Use raw f-strings by default

```python
rf'...'
```

This reduces backslash escaping mistakes.

### 7.2 Double LaTeX braces inside f-strings

- Python variables: `{x}`
- Literal LaTeX braces: `{{` and `}}`

```python
rf'\textbf{{{label}}}'   # correct → \textbf{<value>}
rf'\textbf{{label}}'     # wrong   → \textbf{label}
```

### 7.3 Keep math expressions inside math mode

```python
# Wrong
rf'$\sigma_{{v,Ed}}$ = {x}\,\mathrm{{MPa}}$'

# Correct
rf'$\sigma_{{v,Ed}} = {x}\,\mathrm{{MPa}}$'
```

### 7.4 Do not split LaTeX commands across strings

Avoid building fragile fragments:

```python
part1 = r'$\sigma_{v,Ed}'
part2 = rf' = {x}'
part3 = r'\,\mathrm{MPa}$'
```

Prefer a single coherent LaTeX string wherever possible.

### 7.5 Use `pathlib.Path` for all file paths

```python
from pathlib import Path
tex_file = workdir / "nachweis.tex"
```

Never concatenate paths with `+` or string arithmetic.

---

## 8. Classic LaTeX pitfalls in this stack

### 8.1 Raw Unicode math under `pdflatex`

With `pdflatex`, do not use raw Unicode mathematical characters in LaTeX strings:

- `σ`, `η`, `τ`, `²`, and similar

Use math mode instead:

- `σ_v,Ed` → `$\sigma_{v,Ed}$`
- `η_max` → `$\eta_{\max}$`
- `N/mm²` → `$\mathrm{N/mm^2}$`

Typical error symptom:

```
! Package inputenc Error: Unicode character σ (U+03C3) not set up for use with LaTeX.
```

### 8.2 LaTeX math commands outside math mode

Commands such as `\mathrm`, `\sigma`, `\eta`, `\leq` are only valid inside `$...$`.

```latex
25.9\,\mathrm{kN/cm^2}        % wrong — outside math
$25.9\,\mathrm{kN/cm^2}$      % correct
```

Typical error symptoms (may vary by LaTeX version and package):

- `! Missing $ inserted`
- `\mathrm allowed only in math mode`

### 8.3 `tabularx` / `array` failures

Errors such as `Runaway argument`, `\TX@get@body`, or `Package array Error` typically
come from:

- broken `tabularx` column specs
- too many or too few braces
- malformed `\newenvironment` (see §6.3)
- `breakable` tcolorbox inside `\newcommand` (see §6.5)

### 8.4 `LastPage undefined`

Usually not fatal. Appears on the first pass; disappears after the second pass when
the document compiled cleanly on the first pass (exit code 0).

Do not treat `LastPage undefined` as a root cause. Read the `.log` instead.

### 8.5 `Overfull \hbox` / `Underfull \hbox`

Not fatal. Fix only when they visibly damage the final output.

### 8.6 Python `SyntaxWarning` for escape sequences

In non-raw strings, `\,` and similar combinations cause:

```
SyntaxWarning: invalid escape sequence '\,'
```

Always use raw strings (`r"..."`) for LaTeX content, or double the backslash.

### 8.7 Symbol legend table overflow (`Overfull \hbox`)

The `_sym_legend()` helper in `latex/base.py` renders a compact table of symbol
definitions after equation blocks. A common mistake is setting the layout to
**3 symbol-description pairs per row** (6 columns). Engineering descriptions in German
are typically 5–7 cm wide. Three pairs × ~8.6 cm/pair ≈ 26 cm, which overflows the
~16.6 cm A4 text block by ~10 cm.

**Safe layout: 2 pairs per row (4 columns).**

Two pairs × ~8.6 cm ≈ 17 cm — within A4 text width with a small margin.

Correct column spec:
```latex
@{} >{$}l<{$} @{\;} l @{\quad} >{$}l<{$} @{\;} l @{}
```

Wrong (3-pair) column spec:
```latex
@{} >{$}l<{$} @{\;} l @{\quad} >{$}l<{$} @{\;} l @{\quad} >{$}l<{$} @{\;} l @{}
```

The grouping in the Python generator must match:

```python
# Correct: 2 per row
for i in range(0, len(symbols), 2):
    chunk = symbols[i:i + 2]
    while len(chunk) < 2:
        chunk.append(("", "", ""))

# Wrong: 3 per row — overflows A4
for i in range(0, len(symbols), 3):
    chunk = symbols[i:i + 3]
```

This failure is **silent**: the document compiles and produces a PDF, but the legend
table bleeds into the right margin. It only appears as an `Overfull \hbox` warning
in the `.log`, which is easy to miss. Always visually inspect symbol legend output
on a representative page.

---

## 9. Path handling and platform safety

Always use `pathlib.Path` for:

- working directories
- asset paths
- generated `.tex` and `.pdf`
- portable MiKTeX discovery
- bundle export assembly

```python
from pathlib import Path
workdir = Path(workdir)
tex_file = workdir / "nachweis.tex"
pdf_file = workdir / "nachweis.pdf"
```

---

## 10. Portable `pdflatex` compatibility on Windows

### 10.1 Goal

The system should work with:

- `pdflatex` in `PATH`
- manually configured path in Streamlit
- environment variable
- portable MiKTeX

### 10.2 Recommended resolution order

1. explicit path passed to backend
2. environment variable, e.g. `BALKONSYSTEM_PDFLATEX`
3. local machine config
4. `shutil.which("pdflatex")`
5. known portable locations

### 10.3 Typical Windows paths

```text
C:\PortableLatex\MiKTeX\texmfs\install\miktex\bin\x64\pdflatex.exe
C:\miktex-portable\texmfs\install\miktex\bin\x64\pdflatex.exe
D:\PortableLatex\MiKTeX\texmfs\install\miktex\bin\x64\pdflatex.exe
<repo>\PortableLaTeX\MiKTeX\texmfs\install\miktex\bin\x64\pdflatex.exe
<repo>\MiKTeX\texmfs\install\miktex\bin\x64\pdflatex.exe
<repo>\tools\MiKTeX\texmfs\install\miktex\bin\x64\pdflatex.exe
```

### 10.4 UX recommendation

In Streamlit, provide:

- text field for `pdflatex.exe` path
- "Auto detect" button
- "Test" button using `pdflatex --version`
- machine-local persistence — not project YAML persistence

### 10.5 What not to do

Do not store the `pdflatex` path inside project YAML. That is machine config, not
project data.

---

## 11. Compilation strategy and cleanup

### 11.1 Preferred strategy

Compile inside a temporary working directory:

1. write `.tex`
2. copy required assets
3. run `pdflatex`
4. collect `.pdf`
5. copy only necessary outputs

### 11.2 If a persistent workdir is required

Implement explicit cleanup of `.aux`, `.log`, `.out`, `.toc`, `.fls`, `.fdb_latexmk`
after a successful run, while preserving `.pdf`, `.tex` (when needed), and assets.

### 11.3 Multi-pass rule — IMPORTANT

**Run a second `pdflatex` pass only if the first pass completed successfully**
(exit code 0) or produced only expected warning-level output such as
`LastPage undefined` or `TOC` stabilization warnings.

If the first pass exits with a real compile error (exit code ≠ 0), debug that error
first. Do not blindly launch a second pass — it will not fix compilation errors, and
may obscure the root cause.

For TOC, `LastPage`, or cross-references: two passes are sufficient after the first
clean pass.

---

## 12. Debugging workflow: read the `.log`, do not guess

**This is a hard rule.**

If `pdflatex` returns a failure code:

1. do not guess the root cause
2. do not immediately rewrite random LaTeX
3. open the `.log` file from the working directory
4. inspect the last relevant lines first
5. identify the exact failing macro, environment, or package context
6. only then change Python or LaTeX code

Recommended minimum: read the last ~50 lines of the log. Search upward for the first
real fatal context.

### Typical error signatures

| Error | Look for |
|---|---|
| `\TX@get@body` | `tcolorbox` breakable in `\newcommand` (§6.5) |
| `File ended while scanning` | same as above, or unclosed environment |
| `Runaway argument` | `tabularx` column spec, or malformed environment (§6.3) |
| `Missing arg` | broken macro arguments or column spec |
| `Undefined control sequence` | missing macro or unsupported package |
| `Missing $ inserted` | math command outside math mode (§8.2) |
| `Unicode character ... not set up` | raw Unicode in LaTeX string (§8.1) |
| `LastPage undefined` | first-pass warning, not root cause (§8.4) |

---

## 13. Package governance

Do not add new `\usepackage{...}` dependencies inside individual module renderers.

Any new package dependency must be:

1. justified by a real need
2. added centrally in the base preamble
3. checked for compatibility with the target portable MiKTeX setup
4. avoided entirely when an existing package already solves the problem

This keeps the report environment reproducible.

---

## 14. Frozen dataclass rule

Some selection and state dataclasses in this codebase use `frozen=True`.
**Do not mutate them in place.**

```python
# Wrong — FrozenInstanceError at runtime
sel.stahl.include = True

# Correct
import dataclasses
sel = dataclasses.replace(sel,
    stahl=dataclasses.replace(sel.stahl, include=True))
```

This applies in tests, in pages, and in any code that builds a `ReportSelection`.

---

## 15. Streamlit integration pattern per module

Each new module should follow this flow:

1. new page in `pages/NN_Module.py`
2. user inputs
3. input dataclass construction
4. engine call
5. lightweight visual summary
6. save to session state
7. standalone export `.tex/.pdf/.zip`
8. integration into `pages/04_Protokoll.py`
9. project persistence in `projectio/mapper.py`

---

## 16. Session state

For every new module, add in `ui/session.py`:

- `save_<module>_state(**kwargs)`
- `load_<module>_state()`

Store: relevant input values and a snapshot of results.

Do not store: full LaTeX render strings, binary figures, non-serializable objects.

---

## 17. YAML project persistence

In `projectio/mapper.py`:

- add keys to the module map
- add `_build_<module>_module(...)`
- add `_apply_<module>(...)`
- integrate into `build_project_document(...)`
- integrate into `apply_project_document(...)`

### Backward compatibility rule

Older projects without a module must still load cleanly.

```python
# Correct — safe fallback when module is absent from project doc
hilti_data = doc.get("stuetzenfuss_hilti")   # returns None if absent
if hilti_data:
    state = _apply_hilti(hilti_data)
```

Never assume a key is present in a project document loaded from disk.

---

## 18. Combined report

### 18.1 Expected structure

Stay as close as reasonably possible to the sample report:

- unnumbered cover page
- unnumbered table of contents
- numbered sections 1–6 for the general part:
  - `1 Allgemeines`
  - `2 Vorschriften und Literatur`
  - `3 Baustoffe`
  - `4 Software`
  - `5 Querschnittwerte`
  - `6 Lastannahmen`
- numbered technical chapters thereafter
- final numbered summary chapter
- signature block

### 18.2 Final chapter

Include:

- summary table by module (with `\IOstatus` / `\NIOstatus` / `\HINWEISstatus`)
- open points / Ergebnislage block
- `\resultbox` for Gesamtbewertung
- `\resultbox` for scope limits
- `\resultbox` for Schlussfolgerung
- signature block with ruled lines

### 18.3 Module selection

`report_selection.py` must clearly distinguish between standard report modules and
legacy modules. Do not remove old modules because they are absent from the current
sample report.

### 18.4 Combined report neutrality rule

For the combined Spittelmeister report:

- do not use green/red pass-fail color semantics
- do not use `OK✓`, `NICHT OK`, or dashboard-style badges
- do not use `erfüllt / nicht erfüllt` in status cells
- prefer: `i.O.`, `n.i.O.`, `ergänzend`, or `offen` / `entfällt` where justified

This applies to figures as well.

---

## 19. Figures and plots

Use `latex/report_figures.py` and `report_bundle.py`.

Correct behavior:

- export assets into `report_assets/`
- return `figures`, `extra_files`, and `notes`
- use `\IfFileExists{...}{...}{placeholder}` in generated LaTeX

When exporting for the combined report: remove pass/fail cues from figures; prefer
neutral house-style visual language.

---

## 20. Special modules

### 20.1 Hilti Stützenfuß

Treat as a **structured documentation module** around manufacturer / PROFIS output.
Do not present as a fully independent anchor design solver.

### 20.2 Isokorb

Treat as a product-based, tabulated verification module. If manufacturer data is
missing, mark open points explicitly. Do not invent resistances or edge distances.

### 20.3 RFEM

Distinguish clearly between:

- automated output already available
- manual project input still required
- sections not yet automated

The report may resemble the sample without pretending to fully reproduce the original
manual structural workflow.

---

## 21. Editorial rule for Spittelmeister reports

The PDF must be sober, engineering-oriented, and explicit about limits.

### Forbidden final-PDF wording

Do not let implementation or repository language leak into the client-facing PDF:

- `examples/sample_report/main.tex`
- `Ziel-Referenzbericht`
- `Standardmodule` / `Zusatzmodule`
- `Engine-Ergebnis`
- `Repo` / `fallback` / `auto-detected`
- `placeholder`

Prefer headings and wording such as:

- `Einordnung`, `Bewertung`, `Abgrenzung`
- `Zusammenfassende Bewertung`
- `Randbedingungen für die Ausführung`

---

## 22. QA scan — patterns to check before closing a change

Also scan for **equation blocks without a following symbol legend**.
Any `\end{align*}` not followed by a `_sym_legend(` call within ~5 lines in a
module that introduces 3+ symbols is a gap. Automated pattern search alone misses
this — inspect the generated PDF visually for bare equation blocks.

Search in `latex/*.py` for:

```
σ  η  τ  ²                         (raw Unicode math)
\mathrm                             (outside math mode risk)
\subsection*{                       (manual numbering in combined output)
TODO  FIXME  einzufügen             (draft markers)
OK \checkmark  NICHT OK             (app-style status wording)
okgreen  failred                    (color in combined mode — verify context)
breakable  near  \newcommand{       (breakable-in-macro risk — §6.5)
\begin{tcolorbox}  inside  \newcommand{  (same risk)
\begin{tabularx}  inside  \newenvironment opening block  (§6.3)
```

Check for implementation language leaking into generated PDF text:

```
Engine-Ergebnis
examples/sample_report
Ziel-Referenz
Repo
fallback
auto-detected
placeholder
```

Also verify:

- caller/callee signatures match: `export_report_figures(...)`, `combined_report_tex(...)`
- new modules integrated into:
  - `pages/`
  - `ui/session.py`
  - `projectio/mapper.py`
  - `engine/__init__.py`
  - `latex/__init__.py`
  - `pages/04_Protokoll.py`

---

## 23. Smoke tests before closing a change

Minimum repeatable checks:

1. `py_compile` passes on all touched files — no `SyntaxWarning`
2. combined `.tex` generates without Python exception
3. standalone `.tex` generates for at least one representative module
4. brace balance check passes (see §25.7)
5. all existing tests pass
6. `pdflatex --version` is reachable
7. YAML roundtrip: project with and without the new module loads cleanly
8. first `pdflatex` pass exits with code 0 (or only warning-level output)
9. second `pdflatex` pass produces a clean `.pdf`

---

## 24. Execution strategy for agents

Work in layers. Do not attempt everything in one pass.

1. formatting and preamble stability
2. numbering, sectioning, and grammar
3. Streamlit / YAML wiring
4. extension of existing modules
5. new modules
6. final QA

### Good pattern

Change by layer. Verify each layer before moving to the next.

### Bad pattern

"Make everything match the PDF exactly" in a single pass. That produces broken macros,
invented calculations, incomplete wiring, and signature mismatches.

### Golden rule

When the scope is unclear: prefer honesty. Add an explicit scope or limitation block.
Do not sell magic where manual input is still required.

---

## 25. Useful snippets

### 25.1 Correct mathematical expression with unit

```python
rf'$\sigma_{{v,Ed}} = {sigma:.1f}\,\mathrm{{MPa}}$'
```

### 25.2 Correct comparison

```python
rf'$\eta = {eta:.3f} \leq 1{,}0$'
```

### 25.3 Safe `\okbox` / `\failbox` in combined preamble

```latex
\newcommand{\okbox}[1]{%
  \par\vspace{8pt}\noindent
  \colorbox{SPLightGray}{\parbox{\dimexpr\linewidth-2\fboxsep}{%
    \centering\textbf{#1}}}\par\vspace{8pt}}

\newcommand{\failbox}[1]{%
  \par\vspace{8pt}\noindent
  \colorbox{SPLightGray}{\parbox{\dimexpr\linewidth-2\fboxsep}{%
    \centering\textbf{#1}}}\par\vspace{8pt}}
```

Note: both are visually identical in the neutral combined style. The semantic
difference (ok vs. fail) is communicated by the content, not the color.

### 25.4 Safe body-capturing environment (requires `environ` package in preamble)

```latex
\NewEnviron{myblock}{%
  \begin{tcolorbox}[enhanced, breakable, ...]
  \BODY
  \end{tcolorbox}
}
```

Only use this if `environ` is already in the base preamble.

Prefer `\NewEnviron` only when body capture is truly needed — that is, when the
block must accept multi-paragraph content of unknown length. For simple one-shot
result boxes, prefer `\colorbox + \parbox` (§25.3) or a plain `tcolorbox` environment
written directly in the generated LaTeX body. Do not convert every box to
`\NewEnviron` by reflex.

### 25.5 Safe `pdflatex` call from Python

```python
from pathlib import Path
import subprocess

workdir = Path(workdir)

subprocess.run(
    [str(pdflatex_path), "-interaction=nonstopmode", "-halt-on-error", "nachweis.tex"],
    cwd=workdir,
    check=True,
)
```

### 25.6 Log-first debugging pattern

```python
from pathlib import Path
import subprocess

try:
    subprocess.run(
        [str(pdflatex_path), "-interaction=nonstopmode", "-halt-on-error", "nachweis.tex"],
        cwd=workdir,
        check=True,
    )
except subprocess.CalledProcessError:
    log_path = Path(workdir) / "nachweis.log"
    if log_path.exists():
        tail = "\n".join(
            log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-50:]
        )
        raise RuntimeError(f"pdflatex failed. Last log lines:\n{tail}")
    raise
```

### 25.7 Brace balance check (smoke test)

Run this on a generated `.tex` before handing it to `pdflatex`.
Returns `(unclosed_opens, extra_closes)` — both should be 0 for a well-formed file.

```python
from pathlib import Path

def check_brace_balance(tex_path) -> tuple[int, int]:
    """
    Returns (unclosed_opens, extra_closes).
    Both should be 0 for a well-formed LaTeX file.
    unclosed_opens > 0  → a { was never closed
    extra_closes   > 0  → a } appeared with nothing on the stack
    """
    content = Path(tex_path).read_text(encoding="utf-8")
    stack = []
    extra_closes = 0
    i = 0
    while i < len(content):
        ch = content[i]
        if ch == '\\':
            i += 2
            continue
        if ch == '%':
            while i < len(content) and content[i] != '\n':
                i += 1
            continue
        if ch == '{':
            stack.append(i)
        elif ch == '}':
            if stack:
                stack.pop()
            else:
                extra_closes += 1
        i += 1
    return len(stack), extra_closes


# Usage
unclosed, extra = check_brace_balance("nachweis.tex")
if unclosed or extra:
    raise ValueError(f"Brace imbalance: {unclosed} unclosed opens, {extra} extra closes")
```

### 25.8 Safe `TemporaryDirectory` compile pattern (two-pass)

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil, subprocess

def compile_pdf(tex_source: str, output_pdf: Path, pdflatex_path: str) -> None:
    with TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        tex_file = workdir / "nachweis.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        def run_pass(label: str) -> None:
            try:
                subprocess.run(
                    [pdflatex_path, "-interaction=nonstopmode", "-halt-on-error",
                     tex_file.name],
                    cwd=workdir, check=True,
                )
            except subprocess.CalledProcessError:
                log_path = workdir / "nachweis.log"
                tail = ""
                if log_path.exists():
                    tail = "\n".join(
                        log_path.read_text(encoding="utf-8", errors="replace")
                        .splitlines()[-50:]
                    )
                raise RuntimeError(
                    f"pdflatex failed on {label}. Last log lines:\n{tail}"
                )

        run_pass("pass 1")   # debug here if it fails — do not proceed to pass 2
        run_pass("pass 2")   # stabilizes TOC, LastPage, cross-references

        shutil.copy2(workdir / "nachweis.pdf", output_pdf)
```

### 25.9 Symbol legend — correct 2-column layout

Use `_sym_legend()` from `latex/base.py`. Pass a flat list of
`(symbol_latex, description_german, unit)` tuples. Use `"{-}"` for dimensionless.

```python
from latex.base import _sym_legend

legend = _sym_legend([
    (r'N_{ed}',      'Bemessungsnormalkraft',            'kN'),
    (r'\bar{\lambda}', 'Bezogener Schlankheitsgrad',   '{-}'),
    (r'\chi',       'Abminderungsbeiwert Knicken',       '{-}'),
    (r'N_{b,Rd}',    'Bemessungswert der Knicklast',      'kN'),
    (r'L_{cr}',      'Knicklänge',                       'cm'),
    (r'i',           'Trägheitsradius',                  'cm'),
])
```

Place the result immediately after the closing `\end{align*}` or `\]`, before the
next `\resultbox` or `\vspace`.

The function always renders **2 pairs per row**. Do not change this to 3 — see §8.7.

---

## 26. Anti-patterns summary

| Pattern | Risk | Section |
|---|---|---|
| `breakable` tcolorbox inside `\newcommand` | Fatal crash on large documents | §6.5 |
| `OK✓`, `NICHT OK`, green/red badges in combined report | App semantics leak into reviewer document | §18.4 |
| `tabularx` across `\newenvironment` boundary | Runaway argument | §6.3 |
| Raw Unicode math in LaTeX strings | inputenc error | §8.1 |
| `\mathrm` outside `$...$` | Missing $ inserted | §8.2 |
| Non-raw Python string with `\,` or `\n` | SyntaxWarning / corrupted LaTeX | §8.6 |
| Second `pdflatex` pass on a failed first pass | Masking root cause | §11.3 |
| Inventing checks when data is missing | Trust damage | §4.2 |
| Implementation wording in final PDF | Professionalism issue | §21 |
| `pdflatex` path in project YAML | Machine config leak | §10.5 |
| `dataclasses` frozen mutation | `FrozenInstanceError` | §14 |
| New `\usepackage` in module renderer | Reproducibility risk | §13 |
| 3-column `_sym_legend` layout | `Overfull \hbox` ~10 cm on A4 | §8.7 |