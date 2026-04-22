# Skill: German Engineering Report House Style (Anonymized, Reviewer-Oriented)

## Purpose

Use this skill to write German engineering reports in a formal, calculation-driven, technically restrained style typical of specialist reports in structural, fire, dynamic, thermal, and finite element engineering.

This skill reproduces the **document logic, tone, and evidentiary discipline** of a conservative German engineering office style while remaining fully anonymized. Do **not** mention any company or firm name in the output.

The output report language is normally **German**, even if this skill is written in English.

---

## Quick fallback prompt (short version)

Use this block when context is tight or instructions are competing:

```text
Write in formal German engineering report style.
Use numbered sections and a sober, reviewer-friendly tone.
State the scope explicitly, including exclusions.
Separate strictly between:
1. given data,
2. assumptions,
3. calculated results,
4. engineering judgment.
Describe only analysis-relevant facts.
Justify simplifications, omitted loads, and modelling assumptions.
Cite norms precisely and distinguish clearly between Eurocode, DIN EN, and National Annex references.
Treat software as a tool, not as authority.
Use restrained wording such as:
"wurde angesetzt", "wurde berücksichtigt", "wird davon ausgegangen, dass", "konnte nachgewiesen werden", "konnte nicht nachgewiesen werden", "ist nicht Gegenstand der Untersuchung".
Avoid promotional, conversational, literary, or overconfident language.
Do not mention any company name.
The result should read like an anonymized German engineering expert report.
```

---

## Core stylistic identity

The report shall be:

- formal, technical, sober, and non-promotional
- highly structured and section-driven
- explicit about scope, assumptions, references, model choices, and limitations
- cautious in claims and precise in wording
- traceable to drawings, standards, calculations, measurements, or simulations
- written for technically literate readers such as clients, Prüfingenieure, reviewers, authorities, and engineers
- free of hype, narrative padding, emotional emphasis, or consultant-style self-display

The text should sound like a careful engineer documenting and justifying a technical assessment, not like someone trying to impress the reader.

---

## What the report must always make clear

A good report in this style allows the reader to answer, without guesswork:

1. What exactly was investigated?
2. What was not investigated?
3. Which documents, norms, and assumptions were used?
4. How was the real system idealized into a calculation model?
5. Which actions, combinations, and material properties were applied?
6. Which result governs?
7. What can be concluded reliably?
8. Which uncertainties, reservations, or scope boundaries remain?

If a paragraph does not help answer one of these questions, remove it.

---

## Document families

Choose the label that best matches the task.

### 1. `Gutachten`
Use for a full expert report with a clear technical question and a formal conclusion.

Typical use:
- fire assessment
- structural verification
- accidental action assessment
- FE-based safety verification

### 2. `Bericht`
Use for a neutral technical report focused on calculations, investigations, or optimization studies.

Typical use:
- design studies
- parameter studies
- thickness optimization
- variant comparison

### 3. `Zwischenbericht`
Use for an interim report documenting the current state of investigation, partial results, or preparation for later stages.

Typical use:
- measurement planning
- preliminary model findings
- interim engineering assessment before final verification

### 4. `Gutachtliche Stellungnahme`
Use for a formal technical opinion on an existing structure, often based on records, inspection, and recalculation.

Typical use:
- reassessment of existing structures
- review of modifications
- reserve capacity evaluation
- retrofit assessment

---

## Non-negotiable writing rules

### Rule 1: Scope first
Always state what is investigated and what is not investigated.

Preferred formulations:
- `Gegenstand der Untersuchung ist ...`
- `Ziel der vorliegenden Untersuchung ist ...`
- `Die Beschreibung beschränkt sich auf ...`
- `... ist nicht Gegenstand der Untersuchung.`
- `Die Nachweise umfassen ... jedoch nicht ...`

### Rule 2: Separate four layers of truth
Always distinguish clearly between:

1. **given project information**
2. **assumptions / modelling choices**
3. **calculated results**
4. **engineering judgment**

Typical markers:
- given data: `gemäß Planunterlagen`, `nach Angaben des Auftraggebers`
- assumptions: `es wird davon ausgegangen, dass ...`, `wurde angenommen`, `wurde angesetzt`
- results: `Die Berechnungen haben gezeigt, dass ...`
- judgment: `Die Unterzeichneten halten es für wahrscheinlich, dass ...`

Never disguise judgment as a computed fact.

### Rule 3: Every simplification needs a reason
If a value is assumed, explain why.
If a simplification is made, explain why it is acceptable.
If a load is omitted, explain why.

### Rule 4: Restrained certainty
Prefer:
- `kann nachgewiesen werden`
- `konnte nicht nachgewiesen werden`
- `wird als unkritisch angesehen`
- `kann nicht ausgeschlossen werden`
- `rechnerisch nicht bestätigt`

Avoid:
- `definitiv`
- `eindeutig bewiesen`
- `perfekt sicher`
- `optimale Lösung`
- `bahnbrechend`

### Rule 5: Software is a tool, not a witness
Write:
- `Es wurde ein 3D-Modell mit ... erstellt.`
- `Die Auswirkungen wurden mit ... simuliert.`

Avoid:
- `Die Software beweist ...`
- `Das Modell zeigt eindeutig ...`

The conclusion belongs to the report author, not to the software.

### Rule 6: Conservative without theatrics
State conservative choices calmly.

Preferred formulations:
- `vereinfachter und auf der sicheren Seite liegender Modellansatz`
- `konservativ angesetzt`
- `ingenieurmäßig angenommen`
- `wurde variiert`
- `nicht weiter verfolgt, da der Einfluss gering war`

---

## Norms, Eurocodes, DIN EN, and National Annexes

This is a frequent failure point for LLMs. Handle it explicitly.

### Core rule
Norms must be cited with a **clear and correct hierarchy**:

1. **Eurocode / EN level** if referring to the European standard itself
2. **DIN EN level** if referring to the German-adopted standard designation
3. **National Annex (NA)** explicitly, when national parameters or nationally defined procedures are used

### Required behavior
- Cite norms with enough precision to identify them clearly.
- Use the **full designation in the references list**.
- Use a **compact form in the body text**.
- Do not merge Eurocode text and National Annex content as if they were the same source.
- If a parameter, factor, spectrum shape, or procedure comes from the NA, say so explicitly.
- If the year/edition matters, include it in the references section.

### Preferred body text patterns
- `gemäß DIN EN 1991-1-4`
- `nach DIN EN 1992-1-1`
- `gemäß DIN EN 1998-1/NA`
- `nach Nationalem Anhang zu DIN EN 1991-1-4`
- `entsprechend Abschnitt ... von DIN EN ...`
- `der nationale Parameter wurde nach DIN EN .../NA angesetzt`

### References list pattern
Use full, auditable entries, for example:
- `DIN EN 1991-1-4: Eurocode 1 – Einwirkungen auf Tragwerke – Teil 1-4: Allgemeine Einwirkungen – Windlasten.`
- `Nationaler Anhang zu DIN EN 1991-1-4.`

### Explicit anti-confusion rule
Do **not** write as if the National Annex were automatically included in every Eurocode statement. If the statement depends on national parameters, mention the NA explicitly.

---

## Default report structure

Use this structure unless the case clearly requires something else:

1. Aufgabenstellung
2. Referenzen
   2.1 Projektunterlagen
   2.2 Technische Baubestimmungen / Normen
   2.3 Literatur / Sonstige Literatur
3. Bauwerksbeschreibung / Konstruktionsbeschreibung
4. Baustoffe / Materialeigenschaften / Materialangaben
5. Lastannahmen und ggf. Bemessungskonzept
6. Modellbeschreibung / Berechnungsmodell
7. Ergebnisse
8. Zusammenfassung / Schlussfolgerung
9. Anhänge (if needed)

Logical order must remain:

**task → references → object → materials → loads → model → results → conclusion**

---

## Section guidance

## 1. Aufgabenstellung

### Purpose
Define the assignment, technical objective, basis of input, method, and scope boundary.

### Include
- object and location
- investigated action or scenario
- purpose of assessment
- basis of geometry / material / loading input
- method or software if central
- exclusions where relevant

### Style
Start directly. No warm-up paragraph.

### Typical wording
- `Für ... wurde eine rechnerische Untersuchung durchgeführt, um ... zu bewerten.`
- `Ziel der vorliegenden Untersuchung ist es, zu prüfen, ob ...`
- `Die geometrischen und stofflichen Randbedingungen wurden den Projektunterlagen entnommen.`
- `... ist nicht Gegenstand der Untersuchung.`

---

## 2. Referenzen

### Purpose
Make the basis of the report auditable.

### Rules
- Separate project documents, norms, and literature.
- Keep entries concise but identifiable.
- Use one citation style consistently.
- Include full designations for norms.

No commentary unless needed.

---

## 3. Bauwerksbeschreibung / Konstruktionsbeschreibung

### Purpose
Describe only what matters for the analysis.

### Include
- structural system
- relevant dimensions
- construction type
- support concept
- interfaces, joints, platforms, attachments, reinforcement, or components relevant to load path and modelling

### Rule
This section is descriptive, not yet analytical.

### Typical wording
- `Das Bauwerk besteht aus ...`
- `Die Beschreibung beschränkt sich auf ...`
- `Die Abmessungen sind in Abb. ... angegeben.`
- `Die Verbindungen erfolgen mit ...`

---

## 4. Baustoffe / Materialeigenschaften

### Purpose
Define the material basis used in the model and checks.

### Include as needed
- material classes
- constitutive laws
- stiffness and strength values
- density, modulus, yield stress, thermal parameters
- source of values
- safety factors if directly relevant

### Typical wording
- `Für ... wurde die Stahlsorte ... angenommen.`
- `Das nichtlineare Verhalten wurde mit ... erfasst.`
- `Werkstoffkennwerte wurden auf Grundlage von ... verwendet.`

---

## 5. Lastannahmen / Bemessungskonzept

### Purpose
Document the loading basis and its transformation into design actions.

### Typical logic
- permanent actions
- variable actions
- special actions
- combinations
- imperfections
- design situation / concept

### Rule
First describe the physical action. Then define the design value. Then explain how it enters the model.

### Typical wording
- `als Flächenlast / Linienlast / Knotenlast angesetzt`
- `gleichmäßig auf ... verteilt`
- `wurde nicht berücksichtigt, da ...`
- `gemäß DIN EN ... angesetzt`
- `für die Nachweise wurde die ständige und vorübergehende Bemessungssituation angesetzt`

---

## 6. Modellbeschreibung / Berechnungsmodell

### Purpose
Explain how the real system was abstracted into a calculation model.

### Include
- software / solver
- model dimensionality
- element types if relevant
- supports and boundary conditions
- mesh / discretization
- joints, contact, bedding, springs, mass idealization
- sensitivity checks and simplifications

### Tone
Matter-of-fact and defensible.

### Typical wording
- `Es wurde ein ... Modell mit dem Berechnungsprogramm ... erstellt.`
- `Es wurde eine räumliche Modellierung gewählt ...`
- `Die Bodensteifigkeit wurde mangels belastbarer Angaben angenommen und variiert.`
- `Der Einfluss lag unter ... %, weshalb die Variation nicht weiter verfolgt wurde.`

---

## 7. Ergebnisse

### Purpose
Present the relevant outputs, not everything the software exported.

### Rule
Start with the governing result, then quantify it.

### Include
- governing case
- maxima / minima
- utilization or criterion comparison
- figure and table references
- short technical interpretation where useful

### Typical wording
- `Die Berechnungen haben gezeigt, dass ...`
- `Die maximale Verformung beträgt ...`
- `Der Einfluss ist ...`
- `Die Ergebnisse sind in Abb. ... bis Abb. ... dargestellt.`

Do not jump prematurely to the final judgment.

---

## 8. Zusammenfassung / Schlussfolgerung

### Purpose
Condense the technical outcome into a review-ready conclusion.

### Include
- what was checked
- what could be shown / not shown
- governing limitation or reservation
- whether assumptions materially affect the conclusion
- practical implication if relevant

### Typical wording
- `... konnte nachgewiesen werden.`
- `... konnte rechnerisch nicht nachgewiesen werden.`
- `Damit erfüllt ... die Anforderung ...`
- `Rechnerisch wurde das aber nicht bestätigt.`
- `Daher kann davon ausgegangen werden, dass ...`

A cautious expert opinion is allowed, but it must be clearly marked as judgment.

---

## Figures, tables, equations, appendices

### Figures
- Reference each important figure in the text.
- Keep captions short and factual.
- Use `Abb.` in German reports.

Example captions:
- `Abb. 1: Vertikalschnitt – Mitte (Angaben in m)`
- `Abb. 4: Berechnungsmodell – 3D-Darstellung von schräg oben`

### Tables
- Use for compact inputs, material values, and summarized results.
- Use `Tab.` in German reports.

Example captions:
- `Tab. 1: Geplante Bewehrungsmengen`
- `Tab. 14: Kombinations- und Teilsicherheitsbeiwerte`

### Equations / compact hand checks
Use them for load derivation, plausibility checks, validation, and code formulas.

Preferred sequence:
1. define inputs
2. compute design value
3. state how the value enters the model

### Appendices
Use appendices for large result tables, software printouts, photos, load lists, and long derivations that would interrupt the core argument.

---

## Few-shot examples

These examples are intentionally generic and short. Their job is to teach tone, not technical content.

### Example: Aufgabenstellung

```text
Für die bestehende Hallenkonstruktion am Standort ... wurde eine rechnerische Untersuchung durchgeführt, um die Tragfähigkeit der Anschlusskonstruktion unter den angesetzten Einwirkungen zu bewerten. Die geometrischen Randbedingungen wurden den vorliegenden Planunterlagen entnommen. Materialkennwerte und Einwirkungen wurden, sofern keine projektspezifischen Angaben vorlagen, auf Grundlage der genannten Regelwerke angesetzt. Die Untersuchung beschränkt sich auf die in den Zeichnungen dargestellte Anschlusszone. Bauzustände sowie montagetechnische Fragestellungen sind nicht Gegenstand der Untersuchung.
```

### Example: Lastannahmen / Bemessungskonzept

```text
Die Eigengewichte der tragenden Bauteile wurden programmintern berücksichtigt. Die veränderliche Einwirkung wurde als gleichmäßig verteilte Flächenlast gemäß DIN EN ... angesetzt und entsprechend der maßgebenden Einwirkungsfläche in Linienlasten für das Stabmodell überführt. Zusätzliche Temperatureinwirkungen wurden nicht berücksichtigt, da für den vorliegenden Nachweisfall kein maßgebender Einfluss zu erwarten war.
```

### Example: Modellbeschreibung

```text
Zur Abbildung des Tragverhaltens wurde ein räumliches Berechnungsmodell mit dem Programm ... erstellt. Die Haupttragelemente wurden als Stabelemente modelliert; die Anschlüsse wurden über nachgiebige Kopplungen mit den angesetzten Federkennwerten berücksichtigt. Mangels belastbarer Angaben zur Lagersteifigkeit wurden typische Werte angesetzt und im Rahmen einer Parameterstudie variiert. Der Einfluss auf die maßgebenden Schnittgrößen lag unter 5 %, weshalb die weitere Auswertung auf Basis des Referenzmodells erfolgte.
```

### Example: Ergebnisse

```text
Die Berechnungen haben gezeigt, dass die maximale Ausnutzung im Lastfallkombinationssatz ... am Anschluss ... auftritt. Für den maßgebenden Nachweis ergibt sich ein Ausnutzungsgrad von ... . Die zugehörigen Verformungen bleiben unterhalb des angesetzten Grenzwerts. Auffällig ist, dass die Beanspruchung maßgeblich durch die angesetzte Lagernachgiebigkeit beeinflusst wird, während die Variation der Nebeneinwirkungen nur einen untergeordneten Einfluss zeigt.
```

### Example: Zusammenfassung / Schlussfolgerung

```text
Im Rahmen der vorliegenden Untersuchung wurde die Anschlusskonstruktion unter den angesetzten Einwirkungen rechnerisch überprüft. Für den untersuchten Zustand konnte die Tragfähigkeit der maßgebenden Bauteile nachgewiesen werden. Die Ergebnisse gelten unter der Voraussetzung, dass die angesetzten Materialkennwerte sowie die modellierten Randbedingungen der Ausführung entsprechen. Hinsichtlich der Lagersteifigkeit verbleibt eine Unsicherheit; die durchgeführte Variation zeigt jedoch keinen maßgebenden Einfluss auf das Gesamturteil. Damit wird der untersuchte Zustand aus rechnerischer Sicht als unkritisch angesehen.
```

---

## Language patterns that fit the style

Use these sentence families often.

### Neutral technical narration
- `Es wurde ... erstellt.`
- `Hierbei erfolgte eine Modellierung unter Annahme von ...`
- `... wurde berücksichtigt.`
- `... wurde angesetzt.`
- `... wurde untersucht.`
- `... wurde nicht berücksichtigt.`
- `... wurde variiert.`

### Scope limitation
- `Die Beschreibung beschränkt sich auf ...`
- `... ist nicht Gegenstand der Untersuchung.`
- `Die Nachweise umfassen ... jedoch nicht ...`

### Source discipline
- `gemäß Planunterlagen`
- `nach Angaben des Auftraggebers`
- `auf Grundlage von ...`
- `in Anlehnung an ...`

### Modeling justification
- `vereinfachter und auf der sicheren Seite liegender Modellansatz`
- `typische Steifigkeitswerte`
- `ingenieurmäßige Annahme`
- `unter Ausnutzung der Symmetrie`

### Result evaluation
- `konnte nachgewiesen werden`
- `konnte nicht nachgewiesen werden`
- `wird als unkritisch angesehen`
- `kann nicht ausgeschlossen werden`
- `rechnerisch nicht bestätigt`
- `deutlich eingehalten`
- `geringfügig reduziert`

---

## Patterns to avoid

Do **not** use language like:

- `wir haben gezeigt`
- `unsere innovative Methode`
- `state of the art`
- `robust and scalable`
- `best practice solution`
- `sehr elegant`
- `offensichtlich`
- `natürlich`
- `perfekt`
- `katastrophal` unless quoting a source

Avoid casual fillers, emotion, hype, and marketing language.

---

## Point of view and person

### Preferred default
Use impersonal constructions and passive voice.

Examples:
- `Die Windlast wurde ... ermittelt.`
- `Die Berechnungen wurden ... durchgeführt.`
- `Es wird davon ausgegangen, dass ...`

### Allowed but controlled
`Die Unterzeichneten` may be used in the conclusion when expressing explicit expert judgment.

### Avoid
- first person singular
- conversational first person plural

---

## Treatment of uncertainty and missing information

Never hide missing data. State it and explain how it was handled.

Preferred sequence:
1. note the missing information
2. state the assumption made
3. explain the basis of the assumption
4. mention conservatism or sensitivity if relevant

Example:

```text
Zur Bodensteifigkeit lagen keine belastbaren Angaben vor, weshalb ein Wert angenommen werden musste. Auf Grundlage typischer Werte für den anstehenden Boden wurde ... angesetzt und um den Faktor ... variiert. Der Einfluss lag unter ... %, weshalb die Variation nicht weiter verfolgt wurde.
```

---

## Numerical style

### General rules
- Use SI units.
- Use German notation in German reports.
- Keep units close to the value.
- Use consistent rounding.
- Show enough digits for traceability, but do not overdo it.

### Typical formatting
- `3,48 m`
- `25,0 kN/m²`
- `E = 200.000 N/mm²`
- `ca. 300 kg`
- `unter 10 %`
- `5 mm`

---

## Final quality gate

Before delivering a report in this style, verify all of the following:

- Scope is explicit.
- Exclusions are explicit.
- Report family is appropriate.
- References are separated into project documents, norms, and literature.
- Norm citations distinguish clearly between DIN EN / Eurocode / National Annex where relevant.
- The object description contains only analysis-relevant information.
- Materials, loads, and model assumptions are traceable.
- Every omitted load or simplification is justified.
- The results section identifies the governing case.
- The conclusion distinguishes between calculation result and engineering judgment.
- The language is restrained and non-promotional.
- No company or firm name appears anywhere.

---

## Minimal skeleton template

```md
# [Gutachten | Bericht | Zwischenbericht | Gutachtliche Stellungnahme]

## 1 Aufgabenstellung
[Object, location, purpose, input basis, method, exclusions]

## 2 Referenzen
### 2.1 Projektunterlagen
[plans, statics, specifications, emails if relevant]

### 2.2 Technische Baubestimmungen / Normen
[codes, including NA where relevant]

### 2.3 Literatur
[literature if needed]

## 3 Bauwerksbeschreibung / Konstruktionsbeschreibung
[system, dimensions, relevant components, supports, interfaces]

## 4 Baustoffe / Materialeigenschaften
[material classes, constitutive assumptions, sources]

## 5 Lastannahmen und ggf. Bemessungskonzept
[permanent actions, variable actions, special actions, combinations, imperfections]

## 6 Modellbeschreibung / Berechnungsmodell
[software, dimensionality, elements, supports, simplifications, sensitivity]

## 7 Ergebnisse
### 7.1 [governing topic]
### 7.2 [next topic]

## 8 Zusammenfassung / Schlussfolgerung
[what was shown, what was not shown, reservations, practical implication]
```

---

## Reusable style prompts

### Short reusable prompt

```text
Write the report in formal German engineering expert-report style. Use numbered sections and a sober, calculation-driven tone. Separate strictly between given data, assumptions, computed results, and engineering judgment. State scope limitations explicitly. Justify simplifications, omitted loads, and modelling assumptions. Cite norms precisely and distinguish clearly between DIN EN, Eurocode, and National Annex references. Use restrained wording such as "wurde angesetzt", "wurde berücksichtigt", "konnte nachgewiesen werden", "konnte nicht nachgewiesen werden", and "ist nicht Gegenstand der Untersuchung". Avoid promotional, conversational, literary, or overconfident language. Do not mention any company or firm name.
```

### Full reusable prompt

```text
Write the report in formal German engineering house style. Use a sober, calculation-driven, reviewer-friendly tone. Structure the report clearly with numbered sections. Distinguish strictly between given data, assumptions, computed results, and engineering judgment. State scope limitations explicitly. Describe only analysis-relevant facts. Justify simplifications and omitted loads. Treat software as a modelling tool, not as authority. Cite norms precisely and distinguish clearly between Eurocode, DIN EN, and National Annex references whenever national parameters are involved. Use restrained wording such as "wurde angesetzt", "wurde berücksichtigt", "wird davon ausgegangen, dass", "konnte nachgewiesen werden", "konnte nicht nachgewiesen werden", and "ist nicht Gegenstand der Untersuchung". Avoid promotional, conversational, literary, or hype-driven language. Do not mention any company or firm name. The result should read like an anonymized German engineering expert report.
```