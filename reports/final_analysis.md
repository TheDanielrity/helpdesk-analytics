# HelpDesk Analytics: informe de hallazgos y conclusiones

**Fase 5.1 · Elaboración: 14 de noviembre de 2026**
**Corte observado de los datos: 14 de marzo de 2023, 14:19:32 UTC**

## 1. Resumen ejecutivo

HelpDesk Analytics integra preparación de datos con Python, almacenamiento y análisis en SQL Server y cuatro páginas de visualización en Power BI Desktop. El análisis comprende **66.691 tickets y 257.508 eventos históricos**. Su finalidad es describir patrones, evaluar la interpretación de los indicadores y proponer líneas de revisión operativa sustentadas en evidencia.

Los resultados más relevantes son los siguientes:

1. **La clasificación por prioridad tiene una limitación importante:** 33.965 tickets, el **50,93 %**, tienen prioridad `unknown`. `Medium` concentra otros 24.788 registros, el **37,17 %** del total. La prioridad registrada no permite caracterizar la criticidad de todo el conjunto.
2. **El volumen y los tiempos requieren contexto temporal:** 2016 registra el máximo anual de creaciones, con **7.053 tickets**; 2022 alcanza **6.542**, frente a 5.834 en 2021. Los tickets comienzan en 2007 y los eventos en 2015; 2023 es un período parcial. Estas diferencias impiden interpretar automáticamente las variaciones como cambios de demanda o desempeño.
3. **La distribución del tiempo calendario es muy asimétrica:** en 62.034 tickets con resolución `Done`, la mediana es **35,87 días** y el P90, **2.858,35 días**. Para los 38.747 `Done` creados desde 2016, las cifras son **9,08 y 103,06 días**. La sensibilidad a la composición histórica es considerable; el segundo escenario no sustituye a la base completa.
4. **Las reaperturas observadas varían por prioridad:** 2.123 tickets tienen al menos una visita agregada a `reopened`, el **3,18 %** de 66.691. `Medium` registra **2,19 %** y `Low`, **4,82 %**, con tamaños de grupo diferentes. Hay **2.364 visitas agregadas y 2.325 eventos** de reapertura; los conteos discrepan en 39 tickets.
5. **Las duraciones por estado y la calidad requieren una lectura conjunta:** `open` reúne la mayor suma positiva acumulada; `pending_deployment` presenta la mayor mediana no negativa entre estados, **12,00 días**, sobre 1.413 registros elegibles. Existen **450 tickets con anomalías señaladas**, incluidos 55 con duraciones negativas y 374 con discrepancias de tiempo. Las anomalías se solapan y no deben sumarse como tickets únicos.

Las recomendaciones priorizan revisar la clasificación, validar la semántica de los registros antiguos, estudiar reaperturas y esperas por segmentos comparables y mantener controles de calidad visibles. Son propuestas analíticas: **no se implementaron ni se midieron cambios en procesos empresariales reales**.

## 2. Objetivo del proyecto

Construir un flujo reproducible de análisis de registros históricos de HelpDesk que permita identificar patrones de volumen, prioridades, tiempos calendario, visitas a estados y calidad de datos. El proyecto también busca demostrar capacidades de preparación, modelado, validación y comunicación de resultados para un portafolio profesional.

Las preguntas centrales son: cómo se distribuyen los tickets, cómo cambia su creación en el tiempo, qué tiempos calendario se observan hasta la resolución registrada, cómo se distribuyen las reaperturas y qué estados merecen investigación adicional. El alcance es descriptivo; no se estima el efecto causal de una política ni el impacto de una intervención.

## 3. Metodología y herramientas

El trabajo previo y la revisión de esta fase se apoyan en las siguientes etapas:

1. **Preparación con Python y Pandas.** La limpieza conservó las filas, normalizó fechas a UTC y añadió campos de trazabilidad `__raw` e indicadores `dq_*`. Se preservaron los nulos, `unknown` y las duraciones negativas; no se imputaron valores para mejorar artificialmente los resultados. Véase [Calidad de datos](data_quality.md).
2. **Implementación en SQL Server.** Se cargaron los archivos procesados en `stg.issues` y `stg.issue_change_history`, con claves e integridad referencial verificadas. La carga confirmada y sus comprobaciones se documentan en [Importación SQL Server](sql_load_report.md).
3. **Exploración y análisis avanzado.** Las consultas utilizan agregaciones, CTE, ventanas y percentiles. El historial se preagrupa por ticket antes de unirlo al conjunto de tickets, para evitar multiplicar registros. Fuentes: [SQL exploratorio](../sql/03_exploratory_analysis.sql), [SQL avanzado](../sql/04_advanced_analysis.sql) y sus [resultados exploratorios](sql_exploration.md) y [avanzados](sql_advanced_analysis.md).
4. **Modelado y visualización.** La capa `bi` separa tickets, eventos y parejas ticket–estado. El PBIX local contiene cuatro páginas: **Resumen General**, **Análisis operativo**, **Tiempos por Estado** y **Calidad de Datos**. La estructura de páginas se comprobó mediante lectura del archivo; esta revisión no constituye una auditoría de las fórmulas DAX, filtros o cifras renderizadas en Desktop. Las definiciones de referencia son las de [la capa analítica](bi_data_model.md) y [sus vistas SQL](../sql/05_bi_views.sql).
5. **Verificación del informe.** Se recalcularon desde los CSV procesados los 13 conjuntos de resultados del informe avanzado, con 370 filas de resultados, mediante `expected_results` y `check_results` de [advanced_sql.py](../src/advanced_sql.py). Los conteos, denominadores, sumas decimales y percentiles coincidieron con el informe existente. También se superaron las 26 comprobaciones de conciliación del informe exploratorio mediante `compare` de [explore_sql.py](../src/explore_sql.py). Las reaperturas por prioridad se calcularon adicionalmente en memoria; su reproducción se incluye en el apartado 5.4.

En esta fase no se ejecutaron escrituras en SQL Server ni se regeneraron CSV o informes previos. Las huellas SHA-256 de los cuatro CSV originales y procesados coincidieron al inicio y al finalizar con las documentadas. Se comprobó además la reproducción del código del apartado 5.4 y la existencia de los archivos enlazados. Las cifras del informe se presentan con punto de miles y coma decimal; los porcentajes y días suelen redondearse a dos decimales. Los resultados completos conservan mayor precisión en los informes de origen.

## 4. Descripción del dataset

La fuente documentada es **Help Desk Tickets, versión 3**, de Mohammad Abdellatif, Mendeley Data, DOI `10.17632/btm76zndnt.3`, bajo licencia CC BY 4.0. La atribución y los enlaces al origen se conservan en [README](../README.md#fuente-de-datos-y-atribución); las definiciones están en [FEATURES.md](../data/FEATURES.md).

| Elemento | Alcance verificado |
|---|---|
| Tickets | 66.691 filas; clave `id` única y no nula |
| Eventos históricos | 257.508 filas; clave `id` única y relación `issueid` con tickets sin huérfanos detectados |
| Esquema procesado | 102 columnas en tickets y 28 en eventos, incluidas trazabilidad y calidad |
| Fechas de creación | Del 15/04/2007 al 14/03/2023, en UTC |
| Fechas de eventos | Del 12/08/2015 al 14/03/2023, en UTC |
| Cobertura de historial | 66.650 tickets con al menos un evento; 41 sin eventos observados |
| Resoluciones registradas | 62.034 `Done`; 2.991 `Won't Do`; 661 `Duplicate`; 152 `Cannot Reproduce`; 853 sin resolución |
| Estructura larga de estados | 20 estados × 66.691 tickets = 1.333.820 filas; cada fila representa una pareja ticket–estado |

Se utiliza «ticket» como nombre de la entidad analizada, aunque el dataset incluye distintos usos del sistema. El tipo `Ticket` representa 45.275 registros, el **67,89 %**; también existen `Service`, `Story`, `Vacation`, `Project` y otros. Por ello, no debe interpretarse el conjunto completo como incidencias homogéneas de soporte.

La documentación del proveedor describe enero de 2016 a marzo de 2023 para `issues`, pero los archivos contienen **23.717 creaciones anteriores a 2016**, el **35,56 %**. Se conserva esa diferencia sin atribuirla a migraciones u otras causas no comprobadas. El corte observado es el máximo de las fechas revisadas, no una fecha certificada de extracción ni el estado actual de un HelpDesk.

Fuentes: [Exploración, secciones A, C, E, I y L](sql_exploration.md), [auditoría temporal S](sql_advanced_analysis.md) y [validación de vistas](bi_data_model.md).

## 5. Hallazgos principales

### 5.1. Más de la mitad de los tickets tiene prioridad desconocida

**Qué muestran los datos.** La distribución conserva las etiquetas originales y utiliza como denominador los 66.691 tickets:

| Prioridad | Tickets | % del total |
|---|---:|---:|
| unknown | 33.965 | 50,93 % |
| Medium | 24.788 | 37,17 % |
| High | 4.554 | 6,83 % |
| Highest | 2.084 | 3,12 % |
| Blocker | 656 | 0,98 % |
| Low | 560 | 0,84 % |
| Lowest | 84 | 0,13 % |

Entre los **32.726 tickets con una etiqueta distinta de `unknown`**, `Medium` representa **75,74 %**. Este porcentaje tiene un denominador distinto del 37,17 % mostrado en la tabla; ambos responden preguntas diferentes.

**Qué significa.** El volumen está concentrado en `unknown` y `Medium`. La clasificación disponible ofrece una visión parcial de la criticidad; una comparación operativa por prioridad debe mantener visible el grupo desconocido.

**Limitaciones.** `unknown` no es prioridad baja ni un nulo técnico. Su frecuencia no demuestra un error de captura, y no se ha confirmado que las reglas de prioridad sean equivalentes entre proyectos y años. Tampoco se ha acreditado una escala común que permita fusionar `Highest` y `Blocker`.

**Recomendación.** Revisar la presencia de `unknown` por proyecto, tipo y cohorte de creación; acordar un diccionario de prioridades y criterios de clasificación para una eventual aplicación operativa. No reasignar automáticamente prioridades históricas.

Fuente: [Exploración B](sql_exploration.md); el 75,74 % se deriva de 24.788 / 32.726 × 100.

### 5.2. El volumen cambia entre años y los extremos de la serie son parciales

**Qué muestran los datos.** El máximo anual observado corresponde a **2016: 7.053 creaciones**. Algunos períodos de referencia son:

| Año de creación | Tickets | Consideración |
|---|---:|---|
| 2016 | 7.053 | Máximo anual observado |
| 2019 | 5.084 | Referencia de un año intermedio |
| 2020 | 5.470 | Volumen registrado en la extracción |
| 2021 | 5.834 | Base de comparación con 2022 |
| 2022 | 6.542 | 12,14 % más creaciones registradas que en 2021 |
| 2023 | 1.755 | Sólo hasta el 14 de marzo |

En el detalle mensual de 2023 se observan **749 tickets en enero, 663 en febrero y 343 en marzo parcial**. No se anualiza ese volumen. El inicio en abril de 2007 también hace parcial el primer año.

**Qué significa.** La extracción registra variaciones de volumen y un aumento entre 2021 y 2022. La serie sirve para seleccionar períodos de investigación y comparar composición, pero cuenta creaciones registradas, no tickets resueltos ni productividad.

**Limitaciones.** No se conoce la estabilidad de la cobertura, los proyectos incluidos o las prácticas de registro durante toda la serie. Tener un año calendario completo no garantiza seguimiento completo de sus tickets. En la cohorte de 2023, **408 de 1.755 registros carecen de fecha de resolución**, el **23,25 %**; puede existir resolución aún no observada o información ausente. Los percentiles calculados sólo sobre resoluciones observadas pueden favorecer los casos rápidos de cohortes recientes.

**Recomendación.** Comparar períodos equivalentes por proyecto y tipo, señalar los meses parciales y acompañar las tendencias de tiempos con el tamaño de cohorte, los elegibles y el seguimiento disponible. No atribuir el aumento a mayor demanda real ni una reducción de tiempos a mejoras del servicio sin evidencia adicional.

Fuentes: [Exploración F y G](sql_exploration.md) y [cohortes C](sql_advanced_analysis.md). El 12,14 % se calcula como (6.542 / 5.834 − 1) × 100.

### 5.3. Los tiempos calendario están muy condicionados por la composición histórica

**Qué muestran los datos.** El intervalo se calcula como `issue_resolution_date − issue_created`, con fechas válidas y fin no anterior al inicio. Cada día equivale a 86.400 segundos.

| Población o escenario | Elegibles | Excluidos dentro de su población base | Mediana, días | P90, días |
|---|---:|---:|---:|---:|
| Done: base completa de 62.034 | 62.034 | 0 | 35,87 | 2.858,35 |
| Otras resoluciones: base de 3.804 | 3.804 | 0 | 24,02 | 629,18 |
| Done: sólo creaciones desde 2016, sobre base de 62.034 | 38.747 | 23.287 | 9,08 | 103,06 |
| Done: sin `dq_has_problem`, sobre base de 62.034 | 61.647 | 387 | 35,97 | 2.862,36 |

Los **853 tickets sin resolución registrada** quedan fuera del cálculo calendario elegible. En `Done`, la mediana por prioridad es **9,69 días en `Medium`**, con 22.423 elegibles, y **1.548,28 días en `unknown`**, con 32.414. Los diez intervalos más extensos del análisis avanzado corresponden a creaciones de 2007 con resolución en agosto de 2018, prioridad `unknown` y sin `dq_has_problem`.

**Qué significa.** La separación entre mediana y P90 evidencia una cola de tiempos muy largos. El cambio al seleccionar creaciones desde 2016 muestra que el resumen global es sensible a la mezcla histórica. Excluir las anomalías señaladas apenas cambia esos cuantiles y no resuelve las dudas sobre la interpretación de los registros antiguos.

**Limitaciones.** El intervalo incluye noches, fines de semana, esperas y pausas: **no representa tiempo trabajado**. Una fecha de resolución no identifica necesariamente la primera resolución ni la resolución definitiva tras reaperturas. Las diferencias entre prioridades no controlan antigüedad, proyecto o tipo; no demuestran que una prioridad cause demora. La concentración de fechas antiguas no prueba una migración ni autoriza a corregirlas.

**Recomendación.** Publicar mediana y P90 con elegibles y exclusiones, manteniendo separadas la base completa y las sensibilidades. Investigar la semántica de los casos antiguos con el proveedor y comparar cohortes de seguimiento semejante. No utilizar estos resultados para afirmar cumplimiento de SLA, ahorro de horas o mejora operativa.

Fuentes: [Análisis avanzado A, B, Q y A_MUESTRA](sql_advanced_analysis.md), con definiciones en [SQL avanzado](../sql/04_advanced_analysis.sql).

### 5.4. Las reaperturas difieren por prioridad y sus dos fuentes no son idénticas

**Qué muestran los datos.** Se considera ticket con reapertura agregada aquel con `wfe_reopened > 0`. El denominador incluye los tickets de cada prioridad cuyo agregado es conocido; en esta extracción no hay nulos en ese campo. No se filtra por `Done`, fecha ni calidad.

| Prioridad | Tickets con agregado conocido | Tickets con visita a reopened | % dentro de la prioridad | Visitas agregadas |
|---|---:|---:|---:|---:|
| Blocker | 656 | 15 | 2,29 % | 17 |
| High | 4.554 | 166 | 3,65 % | 190 |
| Highest | 2.084 | 85 | 4,08 % | 93 |
| Low | 560 | 27 | 4,82 % | 46 |
| Lowest | 84 | 4 | 4,76 % | 4 |
| Medium | 24.788 | 542 | 2,19 % | 610 |
| unknown | 33.965 | 1.284 | 3,78 % | 1.404 |
| **Total** | **66.691** | **2.123** | **3,18 %** | **2.364** |

La segunda fuente cuenta eventos con coincidencia exacta `field = status` y `value = reopened`. Identifica los mismos **2.123 tickets**, pero **2.325 eventos**. Su proporción de tickets afectados es **2.123 / 66.650 con historial = 3,1853 %**, frente a **2.123 / 66.691 = 3,1833 %** con el agregado. La igualdad de numeradores no hace intercambiables sus denominadores.

Se detectan **39 tickets con conteos distintos entre agregado e historial**, de 66.650 comparables. La presencia de alguna reapertura coincide ticket a ticket entre ambas fuentes, aunque el número de visitas/eventos discrepe.

**Qué significa.** `Low` presenta la mayor proporción observada y `Medium`, la menor; `unknown` aporta el mayor número absoluto de tickets con reapertura. Volumen y proporción permiten priorizar revisiones diferentes. La proporción de `Lowest` procede de sólo cuatro tickets afectados.

**Limitaciones.** Se observan entradas a `reopened`; no se ha reconstruido para cada caso un cierre previo válido. Un cero no demuestra ausencia de reaperturas fuera de la cobertura disponible. Los tickets anteriores al inicio del historial pueden tener transiciones no observadas. Las diferencias entre grupos no están ajustadas por tipo, proyecto o antigüedad, y no permiten atribuir fallos de resolución a la prioridad.

**Recomendación.** Revisar muestras de `Low` y `Highest`, junto con los 39 casos discrepantes, y contrastarlas con `Medium` dentro de segmentos comparables. Si se dispone de evidencia suficiente, documentar el cierre previo y los motivos de retorno. Mantener separados tickets afectados, visitas agregadas y eventos; no presentar una reducción hipotética de reaperturas como un resultado del proyecto.

**Trazabilidad del desglose.** Los totales y discrepancias proceden de [Análisis avanzado D](sql_advanced_analysis.md). La tabla por prioridad es un cálculo adicional de esta fase sobre `issues_clean.csv`. Puede reproducirse desde la raíz del proyecto con el siguiente código Python, que sólo lee datos y escribe en la salida estándar:

```python
import pandas as pd
from src.clean_data import read_csv

t = read_csv("data/processed/issues_clean.csv")
t["visitas"] = pd.to_numeric(t["wfe_reopened"], errors="raise")
t["con_reapertura"] = t["visitas"].gt(0)
r = t.groupby("issue_priority", dropna=False).agg(
    tickets=("id", "size"),
    conocidos=("visitas", "count"),
    reabiertos=("con_reapertura", "sum"),
    visitas=("visitas", "sum"),
)
r["porcentaje"] = 100 * r["reabiertos"] / r["conocidos"]
print(r.to_string())
```

### 5.5. El mayor tiempo acumulado y la mayor duración típica señalan estados diferentes

**Qué muestran los datos.** `wf_*` contiene segundos acumulados por ticket y estado. La tabla selecciona estados relevantes y calcula cuantiles sólo entre duraciones conocidas y no negativas, incluidos los ceros válidos:

| Estado | Elegibles no negativos | Duraciones nulas | Duraciones negativas | Mediana acumulada, días | P90 acumulado, días |
|---|---:|---:|---:|---:|---:|
| open | 66.613 | 78 | 0 | 1,03 | 2.808,08 |
| in_progress | 36.745 | 29.944 | 2 | 0,18 | 20,24 |
| waiting | 19.704 | 46.987 | 0 | 6,90 | 47,22 |
| validation | 2.961 | 63.730 | 0 | 10,18 | 65,24 |
| pending_deployment | 1.413 | 65.278 | 0 | 12,00 | 88,98 |

`open` presenta la mayor suma positiva acumulada: aproximadamente **4.284.790.352.788,994 segundos**. En cambio, `pending_deployment` tiene la mayor mediana no negativa entre los 20 estados analizados, seguido de `validation`.

**Qué significa.** La suma refleja volumen de registros y duración acumulada; la mediana describe el centro de la distribución entre quienes tienen un valor elegible. `open` reúne muchos más registros y una cola histórica extensa. `pending_deployment` y `validation` son candidatos a investigar por sus duraciones típicas, sin que este ranking pruebe un cuello de botella.

**Limitaciones.** Son acumulados que pueden incluir varias visitas al estado, no intervalos individuales ni horas de dedicación de agentes. Cada estado tiene una población distinta. Los nulos se conservan y no se convierten en cero; para identificar un estado no recorrido se requiere además revisar `wfe_*`. No deben sumarse estas duraciones al tiempo calendario ni dividirse sus sumas entre tickets para inferir esfuerzo laboral.

**Recomendación.** Revisar los casos largos y las reglas de entrada/salida de `pending_deployment`, `validation` y `waiting`; distinguir pausas previstas, dependencias y posibles inconsistencias. Comparar dentro de proyecto, tipo y cohorte antes de proponer cambios de capacidad o escalamiento. Mostrar siempre cobertura, negativos y población elegible junto a los cuantiles.

Fuente: [Análisis avanzado F](sql_advanced_analysis.md). Los días de la tabla se derivan de sus cuantiles en segundos / 86.400; las exclusiones son nulos y negativos de cada estado.

### 5.6. Las anomalías son minoritarias en cantidad, pero los controles no cubren toda duda semántica

**Qué muestran los datos.** Hay **450 tickets con `dq_has_problem = True`**, el **0,6748 %** del total, y **un evento señalado** entre 257.508 eventos. Los controles relevantes incluyen:

| Control | Filas de tickets señaladas | Interpretación |
|---|---:|---|
| Alguna duración de workflow negativa | 55 | Al menos un `wf_*` negativo; no significa tiempo calendario negativo |
| Discrepancia de duración | 374 | `wf_total_time` difiere de `ended − started` por más de 0,000001 segundos |
| Colisión proyecto/número | 65 | Filas que comparten combinación de proyecto y número; no son IDs duplicados |
| Fin posterior al último cambio | 9 | Inconsistencia temporal que requiere revisión |

**44 tickets presentan simultáneamente duración negativa y discrepancia**. Por tanto, 55 + 374 no son 429 tickets distintos. Los 450 corresponden a la unión de anomalías según las reglas implementadas; no se obtienen sumando los conteos de esta tabla. El evento señalado tiene fecha anterior a la creación de su ticket.

No se detectaron IDs duplicados ni eventos huérfanos. Los **853 tickets sin fecha de resolución** y los **41 sin historial** se informan aparte; no son por sí solos anomalías incluidas en `dq_has_problem`. `dq_missing_optional` y `dq_duration_comparable` son indicadores informativos, no pruebas de incorrección.

**Qué significa.** Las claves permiten enlazar las entidades sin problemas de duplicación de IDs detectados. Sin embargo, existen inconsistencias numéricas y temporales que justifican conservar trazabilidad y publicar sensibilidades. La ausencia de flags en casos muy antiguos demuestra que superar estos controles no garantiza una interpretación operativa inequívoca.

**Limitaciones.** Los controles dependen de reglas y tolerancias explícitas. Una discrepancia puede requerir aclarar la semántica de agregación antes de considerarse un error corregible. Su definición compara `wf_total_time` con `ended − started`, **no con creación → resolución ni con la suma de estados**. No debe sumarse el evento señalado a los 450 tickets para formar un total de «casos», pues son unidades diferentes.

**Recomendación.** Mantener un registro de revisión por ID, tipo de advertencia y fuente, confirmar reglas con el proveedor y conservar valores originales. Cualquier exclusión futura debe mostrar cuántos registros aparta y cómo cambia el indicador; no corregir negativos ni eliminar extremos automáticamente.

Fuentes: [Calidad de datos](data_quality.md), [Exploración J](sql_exploration.md) y [Análisis avanzado Q_FLAGS](sql_advanced_analysis.md).

### 5.7. Estado final, resolución y satisfacción representan conceptos diferentes

**Qué muestran los datos.** `closed` agrupa 56.344 tickets y `done`, 9.714 como estados finales. La resolución `Done`, en otra columna, aparece en 62.034 tickets, el **93,02 %**. Hay **220 tickets en estado `closed` o `done` sin resolución registrada**: 192 y 28, respectivamente. También existen tickets en esos estados con resolución `Won't Do` o `Duplicate`.

**Qué significa.** El cruce de columnas demuestra que el estado final no sustituye al resultado registrado. La proporción `Done` describe una clasificación del origen; no mide satisfacción del usuario, resolución al primer contacto ni cumplimiento de compromisos.

**Limitaciones.** No se analizaron encuestas de satisfacción, objetivos contractuales ni evidencia que confirme el resultado percibido. Una resolución ausente tampoco demuestra por sí sola que el ticket siga abierto en el corte. Estos atributos finales no reconstruyen un backlog histórico diario.

**Recomendación.** Nombrar la medida «tickets con resolución Done» y mantener otras resoluciones y ausencias visibles. Para una aplicación futura, definir satisfacción, SLA y cierre con sus propias fuentes y reglas, antes de añadirlos al tablero.

Fuentes: [Exploración D, E y K](sql_exploration.md).

## 6. Interpretación de indicadores

Los denominadores deben recalcularse bajo los filtros activos de proyecto, tipo, prioridad y fecha. Las siguientes bases corresponden a la extracción completa:

| Indicador | Población, fórmula o regla | Lectura correcta |
|---|---|---|
| Total de tickets | 66.691 filas de la entidad tickets | No contar eventos o filas ticket–estado como tickets adicionales |
| Distribución de prioridades | Tickets de cada prioridad / 66.691 | Incluye `unknown`; excluirlo exige declarar otro denominador |
| Resolución Done | 62.034 / 66.691 = 93,0170 % | Clasificación registrada, no satisfacción |
| Mediana y P90 calendario Done | Cuantiles de creación → resolución sobre 62.034 `Done` elegibles | Mediana: centro de la distribución; P90: percentil 90 interpolado, no plazo contractual |
| Calendario de otras resoluciones | Cuantiles sobre 3.804 elegibles | Se informa separado; no se agrega como éxito |
| Tickets con visita agregada reopened | 2.123 / 66.691 con agregado conocido | Cada ticket cuenta una vez; las 2.364 visitas son otra magnitud |
| Tickets con evento reopened | 2.123 / 66.650 con historial | Cada ticket afectado una vez; los 2.325 eventos son otra magnitud |
| Discrepancia de reaperturas | 39 / 66.650 comparables | Requiere historial y agregado conocido |
| Cobertura de historial | 66.650 / 66.691 = 99,9385 % | Al menos un evento; no garantiza todas las transiciones |
| Cuantiles acumulados por estado | Valores `wf_estado ≥ 0` conocidos, por estado | Poblaciones de la tabla 5.5; no incorporar nulos como ceros |
| Promedio por visita de un ticket | `wf_estado / wfe_estado`, sólo con duración ≥ 0 y visitas > 0 | La mediana de estos cocientes no es la media ponderada de todas las visitas |
| Tickets con anomalías | 450 / 66.691 = 0,6748 % | Unión de flags de problema, con posibles solapamientos |

Los percentiles siguen interpolación lineal y pueden no corresponder a un ticket concreto. No se obtiene la mediana global promediando medianas por prioridad o cohorte. Los negativos de workflow se conservan en la auditoría y en las sumas firmadas; se excluyen explícitamente de los cuantiles no negativos.

En Power BI, las medidas a nivel ticket deben respetar el grano de `bi.vw_tickets`; las tablas de eventos y estados tienen relaciones 1:* con filtro desde tickets. Un filtro aplicado sólo a una tabla hija no redefine automáticamente el conjunto de tickets de una medida. La precisión decimal del modelo visual tampoco sustituye la auditoría exacta de SQL. Véanse [modelo y denominadores](bi_data_model.md) y [guía de configuración](../powerbi/model_setup.md).

## 7. Limitaciones del análisis

- **Cobertura histórica desigual.** Los eventos empiezan años después que las creaciones. Incluso los tickets creados desde el inicio del historial pueden tener transiciones ausentes. No se considera completa ninguna historia sólo por contener eventos.
- **Cohortes con diferente seguimiento.** Los casos recientes pueden no haber alcanzado una resolución observada al corte. Los cuantiles de resoluciones observadas no son estimaciones de supervivencia ni corrigen la censura.
- **Mezcla de registros.** Se combinan proyectos, tipos y prioridades con tamaños diferentes. Los grupos pequeños y `unknown` limitan las comparaciones; no se han aplicado ajustes estadísticos ni pruebas de significación para atribuir diferencias.
- **Semántica temporal.** El tiempo calendario incluye pausas y períodos no laborales. Los acumulados de workflow y `started`/`ended` responden a definiciones del origen y no acreditan dedicación efectiva. No se incorporó un calendario laboral validado ni objetivos SLA.
- **Calidad y ausencias.** Los flags no cubren todas las dudas posibles. Las anomalías se solapan y los campos opcionales vacíos no equivalen a registros incorrectos. No se cuenta con una explicación confirmada de las fechas antiguas o de las discrepancias.
- **Resultados de negocio no observados.** No se infiere satisfacción, coste, productividad de agentes, calidad percibida o impacto económico desde `Done`, eventos de asignación o duración de estados. Los eventos `assignee` tampoco prueban reasignaciones efectivas.
- **Alcance de verificación.** Esta fase contrasta los CSV con informes SQL ya ejecutados; no certifica el estado actual del servidor ni audita el cálculo de cada visual del PBIX. El corte es observado, no certificado. Los informes anteriores documentan consultas SQL secuenciales, sin snapshot transaccional ante escrituras concurrentes.
- **Sin evaluación causal o de intervención.** El proyecto analiza una extracción histórica. Las recomendaciones no fueron implantadas ni evaluadas en una organización real.

## 8. Recomendaciones

Las prioridades siguientes son propuestas de revisión, no resultados empresariales ni compromisos de mejora cuantificados.

| Prioridad propuesta | Acción | Evidencia que la justifica | Cómo evaluar una eventual aplicación |
|---|---|---|---|
| Alta | Acordar criterios de prioridad y revisar `unknown` por proyecto, tipo y año | 50,93 % del conjunto está en `unknown` | Seguir la proporción sin clasificación por cohorte y revisar la coherencia con criterios documentados; conservar el histórico original |
| Alta | Aclarar fechas y semántica de registros antiguos con el proveedor | Mediana/P90 Done de 35,87/2.858,35 días frente a 9,08/103,06 desde 2016 | Documentar hallazgos por ID y comparar sensibilidades con poblaciones explícitas, sin elegir el filtro que produzca mejores cifras |
| Alta | Establecer revisión de anomalías con trazabilidad y reglas de aceptación | 450 tickets señalados; negativos, discrepancias y colisiones que se solapan | Verificar casos únicos, persistencia del problema y efecto sobre indicadores antes de aprobar cualquier corrección |
| Media | Revisar reaperturas en segmentos comparables y conciliar ambas fuentes | Diferencias por prioridad; 39 tickets discrepantes | Confirmar cierre previo y motivos de retorno; comparar tasas con denominadores y seguimiento equivalentes |
| Media | Investigar esperas y reglas de salida de estados | Medianas de 12,00 días en `pending_deployment`, 10,18 en `validation` y 6,90 en `waiting` | Examinar casos y dependencias; después observar mediana, P90 y cobertura por segmento, sin atribuir cambios a una acción sin diseño de evaluación |
| Transversal | Publicar contexto junto a cada indicador y conciliar los visuales | Cobertura temporal desigual y poblaciones distintas | Comprobar base sin filtros y escenarios filtrados contra SQL; mostrar elegibles, ausencias, corte y definiciones |

Para una futura implantación operativa, convendría definir responsables de validación, registrar motivos de espera y reapertura y acordar fuentes independientes para satisfacción y SLA. Sólo después de disponer de una línea base comparable y seguimiento suficiente podría evaluarse una intervención. No se proponen metas numéricas de reducción porque este análisis no las justifica.

## 9. Conclusiones

HelpDesk Analytics permite describir de forma trazable el volumen y las características de 66.691 tickets y enlazarlos con 257.508 eventos. La combinación de Python, SQL Server y Power BI ofrece una base para comunicar indicadores sin perder de vista su granularidad, sus denominadores y sus condiciones de elegibilidad.

El análisis identifica una clasificación incompleta de prioridades, variaciones temporales que requieren contexto y una marcada sensibilidad de los tiempos calendario a los registros históricos. También muestra diferencias de reapertura que merecen revisión y estados con duraciones acumuladas elevadas entre quienes los recorren. Estos resultados orientan preguntas operativas; no demuestran por sí solos ineficiencia, causas de demora ni efectos de una política.

La calidad se trata como parte del análisis: se preservan 450 tickets señalados y un evento señalado, se documentan solapamientos y se distingue ausencia de datos de anomalía. La trazabilidad y las sensibilidades permiten valorar la solidez de los resultados sin ocultar registros que producen indicadores menos favorables.

El aporte demostrable del proyecto al portafolio es el desarrollo de un flujo analítico reproducible, una implementación SQL validada, cuatro páginas de visualización y un informe con recomendaciones justificadas. No se atribuyen mejoras de servicio, reducciones de tiempo ni cambios empresariales reales a este trabajo.
