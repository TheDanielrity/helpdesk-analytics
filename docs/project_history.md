# Historial técnico de HelpDesk Analytics

Este documento conserva las entregas originales de las fases 3, 4 y 6. Los pendientes y las referencias a «esta fase» describen cada etapa, no el estado actual del proyecto. Todos los comandos se ejecutan desde la raíz del repositorio.

[Volver al README](../README.md) · [Estado actual de publicación y seguridad](../README.md#estado-de-publicación-y-seguridad)

## Fase 3.1: preparación de SQL Server

Archivos principales:

- `sql/01_create_database.sql`: crea HelpDeskAnalytics sólo si no existe, desde master y fuera de una transacción explícita.
- `sql/02_create_tables.sql`: crea el esquema stg y las tablas faltantes; no modifica tablas preexistentes ni carga registros.
- `reports/sql_schema.md`: diccionario exhaustivo de las 102 columnas de issues y 28 de histórico, tipos, nulabilidad, longitudes, escalas y hashes de los CSV inspeccionados.
- `reports/sql_environment.md`: comprobaciones reales del entorno y diagnóstico pendiente.
- `src/sql_connection.py`: configuración por variables de entorno y prueba con SELECT exclusivamente.
- `src/prepare_sql_schema.py`: genera el DDL y el diccionario tras validar todos los valores de los CSV; no requiere SQL Server ni modifica CSV.
- `tests/test_sql_schema.py`: pruebas del contrato, precisión, cobertura de columnas, claves y configuración.

El modelo es `stg.issues(id)` **1:N** `stg.issue_change_history(issueid)`. Cada tabla tiene PK clustered en id y la segunda una FK sin cascadas. Las fuentes actuales tienen claves no nulas y únicas, sin huérfanos. No se declara UNIQUE para proyecto/número (65 filas con colisiones), ni para change_group_id. El único índice adicional es `(issueid, created)` para joins y secuencia temporal; otros índices dependerán de las consultas y sus planes.

Se usa BIGINT para IDs, contadores integrales y dq_source_row; DATETIMEOFFSET(7) para fechas con UTC; DECIMAL(38,16) para wf_* (hasta 16 decimales observados, sin redondeo ni FLOAT); NVARCHAR(256) para texto y __raw, con longitud UTF-16 comprobada; BIT para los demás dq_*. No se imponen restricciones de duración positiva ni de orden temporal que impidan conservar las anomalías. Los nulos opcionales y unknown permanecen, sin defaults ni imputación. Detalle y justificación en el diccionario.

### Conexión Python

Instalar SQL Server y ODBC Driver 18 en el equipo de ejecución cuando no estén disponibles. La conexión actual funciona con autenticación SQL y `SQL_TRUST_SERVER_CERTIFICATE=yes` para desarrollo local. HelpDeskAnalytics ya existe y tiene los datasets cargados. `reports/sql_environment.md` conserva el diagnóstico histórico; `reports/sql_load_report.md` registra la ejecución exitosa.

Desde PowerShell en la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env  # sólo si .env todavía no existe
# Editar .env localmente: instancia, base master, autenticación y TLS.
.\.venv\Scripts\python.exe src/sql_connection.py
```

El diagnóstico devuelve 0 sólo si conecta y completa SELECT; devuelve 1 si falla o falta configuración. No muestra la cadena de conexión ni contraseñas. `.env` está excluido de Git y `.env.example` contiene sólo ejemplos. Las variables del proceso prevalecen sobre `.env`.

Variables: SQL_SERVER (obligatoria), SQL_DATABASE (master para diagnóstico inicial; luego HelpDeskAnalytics), SQL_DRIVER, SQL_AUTH (windows o sql), SQL_ENCRYPT y SQL_TRUST_SERVER_CERTIFICATE. Con windows se usa la identidad de la sesión. Con sql se requieren SQL_USER y SQL_PASSWORD locales. En este desarrollo local se usa Encrypt=yes y TrustServerCertificate=yes; en otros entornos configurar un certificado confiable y usar TrustServerCertificate=no. El cargador elige master para creación y HelpDeskAnalytics para carga sin editar .env.

### Ejecución manual del DDL cuando la conexión funcione

En SSMS, abrir y ejecutar primero `sql/01_create_database.sql` y después `sql/02_create_tables.sql`. Se requieren permisos para crear bases, esquemas, tablas e índices. Alternativa con sqlcmd instalado y autenticación Windows:

```powershell
sqlcmd -S localhost -E -N -b -i sql/01_create_database.sql
sqlcmd -S localhost -E -N -b -i sql/02_create_tables.sql
```

Reemplazar localhost por la instancia configurada. Estos comandos son una alternativa con autenticación Windows; para la configuración SQL actual utilizar el cargador Python de la sección siguiente. GO es un separador de lotes de SSMS/sqlcmd, no una instrucción que se pueda enviar directamente con pyodbc. Ambos scripts ya se ejecutaron en Fase 3.3 mediante el cargador. El DDL no es una migración de estructuras existentes; el cargador compara el catálogo antes de reutilizarlas y rechaza conflictos.

### Validación sin conexión

```powershell
.\.venv\Scripts\python.exe -m src.prepare_sql_schema
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m sqlfluff parse --ignore-local-config --dialect tsql sql/01_create_database.sql
.\.venv\Scripts\python.exe -m sqlfluff parse --ignore-local-config --dialect tsql sql/02_create_tables.sql
```

La generación vuelve a escribir únicamente el DDL 02 y el diccionario tras comprobar precisión, tipos, claves, longitudes y hashes de los CSV. El parser T-SQL comprueba sintaxis estática, no permisos ni compilación contra el motor. Los CSV grandes siguen excluidos por `.gitignore`.

## Fase 3.3: carga inicial y validación

La carga actual se confirmó: **66.691 tickets**, **257.508 eventos**, **0 IDs duplicados**, **0 huérfanos** y **14.012.706 celdas comparadas exactamente**. Permanecen los 55 tickets con tiempos negativos, 374 discrepancias de duración y demás advertencias de Fase 2. La carga preserva las anomalías documentadas.

Para un entorno nuevo, con los CSV procesados y .env local configurado:

```powershell
.\.venv\Scripts\python.exe -m src.load_to_sql --create-schema
```

Si las tablas ya existen y están vacías, omitir `--create-schema`. También admite `python src/load_to_sql.py`. El tamaño predeterminado es 1.000 filas por lote; `--batch-size` acepta de 1 a 10.000. Se usa `fast_executemany` y `setinputsizes` explícito. `--no-fast` permite evaluar el modo convencional con las mismas comprobaciones; no se activa automáticamente ni ignora errores.

El comando **rechaza tablas con datos** y estructuras incompatibles. La carga actual ya está realizada: un nuevo intento termina sin insertar. No es una herramienta de recarga, reemplazo ni actualización.

El proceso:

1. Lee y valida los CSV como texto, con tipos definidos en el DDL; verifica conteos, columnas, rangos, precisión y relaciones.
2. Comprueba master y el catálogo. Con `--create-schema`, ejecuta sólo los scripts necesarios para objetos ausentes, separando GO fuera de literales/comentarios. Nunca altera objetos para resolver incompatibilidades.
3. Verifica tipos/nulabilidad, PK clustered, FK habilitada y confiable sin cascadas e índice `(issueid, created)`. Rechaza triggers habilitados, columnas identity/calculadas/defaults, CHECK adicionales o índices fuera del contrato.
4. Prueba una selección de registros reales (NULL, negativos, precisión decimal, fechas fraccionarias e indicadores) con el modo ODBC elegido; compara cada celda y hace ROLLBACK. Los eventos de prueba incluyen sus tickets padres.
5. Abre una transacción explícita con `XACT_ABORT ON`, bloquea las tablas con `TABLOCKX,HOLDLOCK` y comprueba nuevamente que estén vacías. Inserta primero tickets y luego eventos con parámetros.
6. Antes de COMMIT compara **todas las celdas**, no sólo muestras, ordenadas por ID. Comprueba conteos, unicidad, huérfanos, NULL por columna, negativos por duración, todos los flags y concordancia con `reports/data_quality.md`. Verifica también que los hashes de los CSV sigan intactos.
7. Confirma una sola vez; consulta desde otra conexión los conteos persistidos y escribe `reports/sql_load_report.md`. Un fallo previo a COMMIT revierte la carga completa. Si se pierde la confirmación del COMMIT, informa estado incierto y exige inspección antes de reintentar. Un intento fallido posterior conserva el reporte exitoso y genera un reporte de intento con fecha.

Conversiones: vacíos/Pandas NA→None→NULL; enteros sin paso por float; True/False→BIT; textos/unknown/__raw intactos. Decimal se valida con precisión de 50 dígitos y se envía como texto Unicode exacto de escala 16 a `CONVERT(DECIMAL(38,16), ?)`. DATETIMEOFFSET usa ISO8601 UTC con siete decimales y conversión SQL explícita para conservar offset y precisión de 100 ns. El formato textual numérico puede cambiar (p. ej. `.0`→`.0000000000000000`); el valor permanece exacto y el CSV original permanece intacto.

La ejecución real utilizó ODBC **18.07.0001** y pyodbc **5.5.0**. La prueba reversible de 88 tickets/5 eventos pasó. Inserción: **30,587 s**; validación completa: **37,618 s**; carga con validación y COMMIT: **68,206 s**; proceso completo: **82,125 s**. No se detectó pérdida de precisión, zona horaria o texto con esta configuración.

Las 25 pruebas locales pasaron, incluidas 13 nuevas de importación (límites numéricos, precisión temporal, NULL, Unicode, GO, rechazo de destinos ocupados e incompatibles, lotes parametrizados y control de transacciones). Las pruebas automáticas no necesitan SQL Server ni insertan datos ficticios en él:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Una carga fallida puede dejar la base y las tablas recién creadas vacías: la creación de base se ejecuta fuera de la transacción de datos. No se eliminan esos objetos. Futuras entradas con claves inválidas requieren un diseño de cuarentena que conserve registros, no ajustes para forzar restricciones. Power BI sigue pendiente.

## Fase 3.4: exploración con SQL

`sql/03_exploratory_analysis.sql` contiene 14 consultas de lectura: catálogo (S), totales (A), prioridad/tipo/estado/resolución (B–E), creación anual y mensual (F–G), top 10 proyectos (H), cobertura de historial (I), flags (J), cruce estado/resolución (K), cobertura temporal (L) y procedencia (M). En SSMS elegir HelpDeskAnalytics antes de ejecutarlo.

Para ejecutar las mismas consultas, comparar los resultados con los CSV mediante Pandas y regenerar `reports/sql_exploration.md`:

```powershell
.\.venv\Scripts\python.exe -m src.explore_sql
```

El reporte conserva todas las distribuciones y los 192 meses observados, explica cada consulta y propone indicadores. Pasaron 26 comprobaciones de conteos, porcentajes, prioridades, tipos, estados, resoluciones, top 10, historial, flags, fechas y procedencia. El parser T-SQL aceptó el archivo. No se modifican datos ni se crean objetos.

Hallazgos: unknown representa 50,9289%; existen 15 tipos distintos; 220 tickets closed/done tienen resolución NULL; 23.717 tickets son anteriores a 2016. Los estados finales no demuestran éxito, y la cobertura temporal real comienza en 2007 pese al intervalo distinto descrito en FEATURES.md. Los porcentajes usan denominadores explícitos y las categorías originales permanecen separadas.

## Fase 3.5: tiempos, reaperturas y estados

Consultas de lectura en `sql/04_advanced_analysis.sql`; definiciones, poblaciones, exclusiones, resultados completos y recomendaciones de visualización en `reports/sql_advanced_analysis.md`. Reproducción y validación independiente:

```powershell
.\.venv\Scripts\python.exe -m src.advanced_sql
```

El ejecutor genera el SQL, calcula resultados desde los CSV con Pandas, ejecuta 14 SELECT/CTE y contrasta 13 conjuntos de resultados (370 filas de comparación), además de auditar UTC y precisión temporal. No modifica registros ni estructuras. Los hashes de raw y processed permanecen intactos. El parser T-SQL aceptó las 14 consultas.

Se usan `DATEDIFF_BIG(MICROSECOND)` para tiempo calendario creación→resolución y `PERCENTILE_CONT` para mediana/P90, con interpolación lineal verificada. No se usa wf_total_time como sustituto del intervalo. Done y otras resoluciones se separan; los flags de workflow sólo filtran escenarios de sensibilidad. El histórico se preagrupa antes de unirlo para conservar una fila por ticket.

Resultados base Done: 62.034 elegibles, mediana **35,8675 días**, P90 **2.858,3523 días**. Otras resoluciones: 3.804 elegibles; 853 tickets sin resolución quedan fuera de los percentiles. La sensibilidad de creaciones desde 2016 conserva 38.747 Done, con mediana **9,0814 días** y P90 **103,0591 días**. No equivale a corregir ni eliminar los tickets anteriores.

Reaperturas: 2.123 tickets con visitas agregadas, 2.364 visitas frente a 2.325 eventos observados y 39 tickets discrepantes. Responsables: 62.706 eventos assignee; mediana global 1 entre tickets con historial; 16.791 tienen múltiples eventos. Los eventos no equivalen automáticamente a reasignaciones efectivas. Se publican por separado duración acumulada por estado, negativos y promedio por visita.

Las cohortes incluyen población total, elegibles Done, fechas de resolución ausentes, parcialidad calendario y seguimiento hasta el corte observado. Un período calendario completo puede tener seguimiento incompleto. Los tiempos son calendario, no laborales; no se calculan SLA ni se concluye ineficiencia a partir de duraciones extensas. Power BI continúa pendiente.

## Fase 3.6: vistas para Power BI

DDL en `sql/05_bi_views.sql`; modelo, diccionario real, denominadores, tipos, relaciones y conexión Desktop en `reports/bi_data_model.md`. El diseño fuente está en `reports/bi_data_model_design.md`.

| Vista | Filas verificadas | Granularidad |
|---|---:|---|
| bi.vw_tickets | 66.691 | Ticket, clave ticket_id |
| bi.vw_ticket_events | 257.508 | Evento, clave event_id; ticket_id asociado |
| bi.vw_ticket_state_durations | 1.333.820 | Ticket × estado, clave (ticket_id, estado); 20 estados |

`vw_tickets` preagrupa eventos por issueid, conserva dimensiones y todos los dq_*, y ofrece tiempos calendario/eligibilidad sin percentiles estáticos. Las fechas se normalizan a UTC y se exponen como DATETIME2(7). `vw_ticket_events` conserva los valores NULL y la auditoría. La vista larga conserva duraciones DECIMAL exactas, negativos, visitas y pares no recorridos con NULL; wf_total_time no es un estado. El texto duracion_segundos_exacta permite auditar precisión que el modelo numérico de Power BI no conserva íntegramente.

Las tres vistas ya existen. El ejecutor sólo crea faltantes, reutiliza definiciones idénticas y rechaza conflictos sin sustituir objetos. Despliegue y validaciones están en una transacción; stg se verifica mediante SHA-256 de todas sus filas/columnas antes y después. Usar sólo generación o aplicar/validar explícitamente:

```powershell
.\.venv\Scripts\python.exe -m src.bi_views
.\.venv\Scripts\python.exe -m src.bi_views --apply
```

Se superaron 20 validaciones SQL, 31 pruebas locales/regresión (6 nuevas de vistas) y 4 pruebas de integración reales de sólo lectura con Pandas. Para repetir pruebas locales:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las cuatro pruebas SQL se omiten salvo activación explícita:

```powershell
$env:HELPDESK_BI_INTEGRATION='1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_bi_views_integration.py -v
Remove-Item Env:HELPDESK_BI_INTEGRATION
```

Para la conexión posterior: Obtener datos → SQL Server → HelpDeskAnalytics → Importar; autenticar mediante Base de datos en el diálogo seguro y elegir exclusivamente las tres vistas bi. Las credenciales de .env no se transfieren a Desktop. Relaciones: tickets[ticket_id] 1→* eventos[ticket_id] y tickets[ticket_id] 1→* estados[ticket_id], filtro único desde tickets. No relacionar eventos con estados ni habilitar bidireccionalidad; los filtros propios de una hija no se propagan hacia la otra. Medianas/P90 se calcularán dinámicamente con elegibilidad y denominadores explícitos. Todavía no se crea el dashboard.

## Fase 4.1: preparación manual del modelo Power BI

Guía: [powerbi/model_setup.md](../powerbi/model_setup.md). Incluye conexión mediante Importar, tipos de cada columna, relaciones 1:* con filtro único desde tickets, validaciones sin DAX, campos de auditoría que podrían ocultarse y advertencias de UTC, precisión y doble conteo.

**Ruta de trabajo prevista del PBIX:** `powerbi/HelpDesk_Analytics.pbix`. Ya existe un archivo local con ese nombre; no fue abierto, modificado ni validado internamente en esta fase. Su presencia no demuestra que el modelo esté configurado. `*.pbix` permanece excluido de Git mediante `.gitignore`.

Los conteos de referencia SQL son 66.691 tickets, 257.508 eventos y 1.333.820 filas ticket–estado. Las comprobaciones de la guía quedan pendientes de realizar y registrar manualmente en Desktop. Esta entrega es documental: no modifica SQL, no controla la interfaz y no crea medidas DAX ni visualizaciones.

## Fase 6.6: estado previo al primer commit

Los dos párrafos siguientes conservan el estado de aquella entrega, antes de aprobar el primer commit y publicar el proyecto. Sus pendientes no describen el estado actual.

La fase 6.6 **inicializó el repositorio Git local en la rama `main`** y preparó 52 archivos revisados para el primer commit. No se creó ningún commit, no se configuraron remotos y no se publicó ni ejecutó push. La revisión cubre el contenido real del staging; si se pretende incorporar otro historial, debe conservarse y revisarse antes de vincularlo.

Las cuatro capturas están integradas y verificadas, los notebooks están validados y las cuatro pruebas SQL pasaron. La fase 6.5 completó la revisión de granularidad de los informes históricos y añadió `LICENSE` MIT 2026, sin alterar resultados. La fase 6.6 revisó las exclusiones y los archivos preparados: el primer commit queda pendiente de aprobación. Publicar o hacer push requiere autorización posterior. Véase [el checklist final de publicación](../reports/publication_checklist.md).

## Fases 6.7 y 6.8: primer commit y publicación

El primer commit, `69b854e`, incorporó los 52 archivos revisados. Se publicó en la rama `main` de [GitHub](https://github.com/TheDanielrity/helpdesk-analytics), con README, licencia, ambos notebooks y las cuatro capturas. La verificación posterior confirmó que el árbol publicado coincidía con el local y que no se habían versionado datos o credenciales excluidos.

El commit posterior `73641b6` retiró del seguimiento `.kin/.gitignore` y `.vscode/settings.json`, e incorporó la exclusión completa de ambas carpetas. Sus copias locales se conservaron; esos dos archivos siguen presentes en el primer commit histórico. La publicación contiene 50 archivos desde ese cambio.
