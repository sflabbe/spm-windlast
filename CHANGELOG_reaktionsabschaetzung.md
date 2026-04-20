# Changelog técnico — Reacciones simplificadas de balcón

## Alcance cerrado
Se cerró la funcionalidad de **reacciones simplificadas** asegurando coherencia entre:
- cálculo en core,
- visualización en Streamlit,
- diagramas,
- reporte PDF,
- tests de regresión.

## Cambios implementados
- Se consolidó la variable geométrica **s = B - 2*b** en el core y en la salida de resultados.
- Se mantuvieron alineadas las expresiones:
  - `q_seite_1 = abs(we_side_pressure) * hw_yz`
  - `q_seite_2 = abs(we_side_suction) * hw_yz`
  - `q_vorne = abs(we_front_suction) * hw_xz`
  - `Hx_k = T * (q_seite_1 + q_seite_2)`
  - `M_A_k = T^2/2*(q_seite_1 + q_seite_2) + q_vorne*B*(B/2 - b)`
  - `Hy_2_k = M_A_k / s`
  - `Hy_1_k = q_vorne*B - Hy_2_k`
- Se unificó la nomenclatura en app y PDF como **“vereinfachte Reaktionsabschätzung”** / **“statische Näherung in Draufsicht”** / **“Vorbemessung”**, evitando presentar el método como “exacto”.
- Se añadió en el PDF una subsección explícita de **formulación e hipótesis estructurales**.
- Se incorporó la **nota técnica obligatoria**:
  > Die nachfolgenden Auflagerreaktionen stellen eine vereinfachte statische Abschätzung in Draufsicht dar. Sie dienen der Vorbemessung und ersetzen kein vollständiges Tragwerksmodell mit exakter Lagerreaktionsbestimmung.

## Regresión numérica validada
Caso de referencia validado en tests:
- `we_side_pressure = 0.760`
- `we_side_suction = -0.369`
- `we_front_suction = -1.227`
- `B = 3.94`
- `T = 1.94`
- `hw_yz = 1.1`
- `hw_xz = 1.1`
- `b = 0.3`

Resultados esperados aproximados (confirmados):
- `q_seite_1 ≈ 0.836`
- `q_seite_2 ≈ 0.406`
- `q_vorne ≈ 1.350`
- `Hx_k ≈ 2.41`
- `M_A_k ≈ 11.22`
- `Hy_2_k ≈ 3.36`
- `Hy_1_k ≈ 1.96`
