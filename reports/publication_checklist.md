# Checklist final de publicación · HelpDesk Analytics

**Fase 6.6 — Inicialización de Git y revisión del staging: 16 de noviembre de 2026.** Estado: repositorio local inicializado en `main`; 52 archivos seguros preparados y revisados. Se conservan la licencia MIT, la revisión de informes, notebooks, capturas y reverificación SQL. **Sin commits, remotos, publicación ni push. El primer commit está preparado y pendiente de aprobación.** Las secciones anteriores conservan su evidencia histórica con el alcance de cada fase.

## Documentación y arquitectura

- [x] README principal actualizado con presentación del proyecto, cifras verificadas y fuentes.
- [x] Sección **Análisis con Jupyter** con ambos notebooks y enlace a su guía.
- [x] Arquitectura documentada: CSV → Python → SQL Server → Power BI; Jupyter calcula desde CSV y contrasta informes SQL sin conectarse al motor.
- [x] Instrucciones de instalación con `.venv`, dependencias de uso y de desarrollo, selección del kernel y pruebas.
- [x] Historial técnico del README conservado en un bloque desplegable. Los nueve informes anteriores permanecen sin cambios.
- [x] Cuatro páginas del PBIX verificadas estructuralmente; sección de capturas reales integrada sin imágenes de sustitución.
- [x] Revisar las cuatro capturas PNG proporcionadas, su información visible y sus metadatos.
- [x] Mostrar las cuatro imágenes en README mediante enlaces relativos con nombres y mayúsculas exactos.
- [x] Comprobar que las capturas estén permitidas por `.gitignore` y que sus huellas SHA-256 permanezcan intactas.

Las páginas son **Resumen General**, **Análisis operativo**, **Tiempos por Estado** y **Calidad de Datos**. Los cuatro enlaces previstos de la fase 6.3 se sustituyeron por las capturas reales de `powerbi/screenshots/`, sin copiar, renombrar ni modificar las imágenes originales.

## Capturas verificadas · Fase 6.4

| Página | Archivo real | Dimensiones | Resultado |
|---|---|---|---|
| Resumen General | [01_resumen_general.png](../powerbi/screenshots/01_resumen_general.png) | 1454 × 849 px | PNG válido; revisión visual completada |
| Análisis Operativo | [02_analisis_operativo.png](../powerbi/screenshots/02_analisis_operativo.png) | 1457 × 848 px | PNG válido; revisión visual completada |
| Tiempos por Estado | [03_tiempos_por_estado.png](../powerbi/screenshots/03_tiempos_por_estado.png) | 1452 × 849 px | PNG válido; revisión visual completada |
| Calidad de Datos | [04_calidad_datos.png](../powerbi/screenshots/04_calidad_datos.png) | 1470 × 850 px | PNG válido; revisión visual y detalle enmascarado documentados |

Los cuatro archivos se decodificaron y verificaron con Pillow, en formato PNG/RGBA y sin metadatos adicionales. Se inspeccionaron visualmente las cuatro páginas: no se observaron nombres personales, correos, contraseñas, rutas del equipo ni datos de conexión.

**Detalle de privacidad:** Calidad de Datos contiene IDs de tickets y códigos de proyecto enmascarados. Se contrastaron en memoria 11 filas visibles con el dataset local público, sin reproducir sus claves en este documento; el diccionario del proveedor documenta el enmascaramiento del proyecto. No se identificaron datos directos de identidad o autenticación. Esa granularidad queda explícita y es distinta de publicar únicamente agregados.

Las tarjetas usan unidades abreviadas y redondeos del dashboard; las capturas no recalculan ni corrigen métricas y no constituyen una auditoría completa de DAX. No se modificaron las imágenes, el PBIX, los análisis, los CSV ni las consultas. Las reglas de exclusión se comprobaron reutilizando metadatos auxiliares preexistentes y excluidos; no se inicializó Git en esta fase.

La validación final de la fase 6.4 confirmó los cuatro enlaces de imagen con coincidencia exacta de nombres y mayúsculas, 28 enlaces locales de archivo en README y checklist sin destinos ausentes, y las cuatro capturas entre los 51 candidatos permitidos por las reglas de Git. Las huellas SHA-256 de los cuatro PNG y de 14 archivos protegidos adicionales permanecieron idénticas; `.gitignore` no necesitó cambios. La comprobación es local y no implica haber publicado o probado un sitio remoto en GitHub.

## Reproducibilidad y pruebas realizadas

| Verificación | Resultado de esta fase | Alcance y limitación |
|---|---|---|
| Suite `unittest discover -s tests -v` | 35 descubiertas: **31 superadas y 4 omitidas** | Las cuatro omitidas son de integración SQL, desactivadas por defecto |
| Intento SQL anterior (fase 6.3) | **Sin ejecutar los casos: SQLSTATE 08001** | Evidencia histórica: falló `setUpClass`; sustituida como estado actual por la reverificación documentada abajo |
| Reverificación SQL del 15/11/2026 | **4 ejecutadas y superadas; 0 fallidas, 0 errores, 0 omitidas** | Conexión fuera del sandbox; tres vistas `bi` accesibles, definiciones intactas y conteos coincidentes antes/después |
| Dependencias | `pip check` sin incompatibilidades | Dependencias existentes suficientes; `requirements.txt` y `requirements-dev.txt` no se modificaron |
| Notebook 01 | 23 celdas Python; **24 controles**; 4 PNG | Kernel nuevo, ejecución secuencial desde la raíz; formato validado |
| Notebook 02 | 20 celdas Python; **47 controles**; 7 PNG | Kernel nuevo; incluye 12 tablas SQL y 364 filas de resultados contrastadas |
| Seguridad de salidas | Sin errores ni `stderr`; tablas máximas de 17 y 20 filas | Fuentes, metadatos, salidas textuales y metadatos PNG revisados; tamaños aproximados de 410 y 638 KiB |
| Integridad | CSV, SQL, PBIX, informes originales, dependencias y `.env` conservados | Huellas locales antes/después; notebooks reejecutados y un ajuste editorial documentado en `FEATURES.md` |

Se mantuvieron las fuentes de cada celda y sus identificadores. Las salidas textuales y tablas antes y después de la reejecución resultaron idénticas. Los contadores, las imágenes regeneradas y los metadatos de ejecución se normalizaron; no se alteraron métricas.

Las dependencias declaradas corresponden al uso real: Pandas, NumPy y Matplotlib para análisis; pyodbc y python-dotenv para SQL; ipykernel, nbformat y nbclient para ejecución y validación de notebooks; SQLFluff en desarrollo. `IPython.display` está cubierto por la dependencia de ipykernel. No se instalaron paquetes adicionales ni se añadió un archivo de bloqueo que no hubiera sido validado.

La comprobación de integración se completó en la reverificación documentada a continuación. Puede repetirse con el comando documentado en [README](../README.md#pruebas-y-estado-de-verificación), desde una sesión con conectividad, controlador y credenciales válidos. El README refleja ahora el resultado satisfactorio y conserva la referencia al intento anterior. Sus consultas son de lectura. No ejecutar los cargadores ni `bi_views --apply` como parte de esta revisión.

## Reverificación SQL Server — 15 de noviembre de 2026

**Resultado actual: conexión verificada; cuatro pruebas superadas; sin bloqueo de SQL Server en la sesión con acceso local.** Ejecución entre las 22:33:01 y las 22:33:06 de Lima (UTC: 16 de noviembre de 2026, 03:33:01–03:33:06). Base comprobada: `HelpDeskAnalytics`; versión del motor: `17.0.1000.7`.

El usuario identificó que el servicio SQL Server estaba detenido durante el incidente anterior. En esta revisión, el diagnóstico dentro del sandbox devolvió `SQLSTATE 08001`; al repetirlo fuera del entorno restringido, la conexión fue satisfactoria. Las pruebas y los conteos siguientes se ejecutaron fuera del sandbox. Por tanto, el fallo de acceso del entorno restringido no se registra como un fallo de las pruebas ni como un bloqueo actual del motor.

Se activó `HELPDESK_BI_INTEGRATION=1` y se descubrió exclusivamente `tests/test_bi_views_integration.py` con `unittest`, sin modificar sus casos. Un ejecutor temporal en memoria mostró únicamente identificadores, estados y totales para evitar mensajes de conexión que pudieran revelar credenciales. Resultado: **4 descubiertas y ejecutadas; 4 superadas; 0 fallidas; 0 errores; 0 omitidas**. Duración de la suite: **2,566 segundos**.

| Prueba de integración | Resultado | Comprobación real |
|---|---|---|
| `test_creation_cohorts_and_history` | Superada | Cohortes mensuales contra Pandas y resumen de tickets/cobertura histórica |
| `test_deployed_definitions_reused_without_ddl` | Superada | Las tres vistas existentes son compatibles con las definiciones esperadas; solo inspección de catálogo |
| `test_filtered_percentiles_against_pandas` | Superada | Conteos, mediana y P90 para los tres filtros definidos en el test |
| `test_long_states_exact_sums_and_missing_values` | Superada | 20 estados; sumas decimales exactas, valores observados, negativos, ceros y estados no recorridos contra el CSV existente |

Los conteos se consultaron mediante `SELECT COUNT_BIG(*)` antes y después de la suite:

| Objeto | Esperado | Antes | Después | Resultado |
|---|---:|---:|---:|---|
| `stg.issues` | 66.691 | 66.691 | 66.691 | Coincide |
| `stg.issue_change_history` | 257.508 | 257.508 | 257.508 | Coincide |
| `bi.vw_tickets` | 66.691 | 66.691 | 66.691 | Accesible; coincide |
| `bi.vw_ticket_events` | 257.508 | 257.508 | 257.508 | Accesible; coincide |
| `bi.vw_ticket_state_durations` | 1.333.820 | 1.333.820 | 1.333.820 | Accesible; coincide |

El catálogo del esquema `bi` devolvió exactamente esas tres vistas. Las huellas SHA-256 de sus definiciones, obtenidas mediante `OBJECT_DEFINITION`, fueron idénticas antes y después. Los conteos estables no equivalen a una auditoría de todas las celdas de la base; esta sesión ejecutó únicamente consultas `SELECT` contra SQL Server.

Un intento auxiliar previo se detuvo antes de ejecutar la suite por asignar el tiempo de espera al cursor de pyodbc. Se corrigió asignándolo a la conexión y la ejecución completa indicada arriba terminó con código 0; ese error del ejecutor no fue un fallo de SQL Server.

No se ejecutaron cargadores, DDL ni `bi_views --apply`; no se modificaron tablas, datos ni vistas, no se regeneraron CSV y no se mostraron ni guardaron contraseñas. La comparación SHA-256 de los 55 archivos protegidos del proyecto permaneció idéntica tras las comprobaciones. Solo se actualizó este checklist como documento del proyecto; no hubo publicación, push, inicialización de Git, staging ni commits.

## Resultados preservados

- [x] 66.691 tickets y 257.508 eventos.
- [x] 33.965 prioridades `unknown`, 50,93 % del total.
- [x] `Done`: 62.034 elegibles; mediana calendario 35,87 días y P90 2.858,35 días.
- [x] `Done` creado desde 2016: 38.747 elegibles; 23.287 excluidos de la base; mediana 9,08 días y P90 103,06 días.
- [x] 2.123 tickets con reapertura, 2.364 visitas agregadas, 2.325 eventos y 39 tickets discrepantes; diferencia neta 39 y absoluta 41.
- [x] 450 tickets con anomalías; 55 con negativos, 374 con discrepancias y 44 con ambas condiciones.
- [x] `pending_deployment`: mediana acumulada no negativa de 12,00 días, n=1.413.
- [x] Denominadores, ausencia de causalidad, censura, cobertura histórica y diferencia entre tiempo calendario y tiempo trabajado explicados.

Las cifras y sus poblaciones están desarrolladas en [el informe final](final_analysis.md) y los notebooks; no se modificaron para forzar coincidencias. `Done` no se presenta como satisfacción ni cumplimiento de SLA.

## Revisión de seguridad y privacidad

- [x] Candidatos enumerados con las reglas reales de Git, incluidos `.gitignore` anidados; los metadatos temporales de la auditoría permanecen dentro de `.venv`, excluidos de publicación.
- [x] `.env`, CSV, `.venv`, PBIX, cachés, credenciales, claves privadas y bases `.kin/local/` excluidos.
- [x] `.env.example` permitido y revisado: campos `SQL_USER` y `SQL_PASSWORD` vacíos, sin secretos reales.
- [x] Búsqueda de rutas personales, correos, patrones comunes de claves API, claves privadas y asignaciones literales de credenciales en los candidatos.
- [x] Comparación de los valores secretos configurados localmente contra el contenido candidato, sin imprimirlos ni registrarlos en documentos públicos.
- [x] Coincidencias revisadas: identificadores de variables de prueba y una contraseña ficticia del test de escape SQL; no son una configuración de autenticación real.
- [x] Notebooks sin columnas de usuarios, proyectos o IDs en sus vistas individuales publicadas, sin valores de asignación, credenciales ni rutas personales en fuentes/salidas.
- [x] `data/FEATURES.md` permitido como documentación pública atribuida; CSV y `data/EXAMPLE.md` permanecen excluidos.
- [x] Bases de Kindex preservadas. No se publicaron conceptos privados ni se regeneraron snapshots de memoria desde un grafo incompleto.
- [x] Staging real revisado en fase 6.6: 52 archivos; contenido del índice contrastado con los archivos revisados y exclusiones verificadas. Si cambia antes del commit, repetir la revisión.
- [ ] Revisar cualquier historial Git existente en otra ubicación antes de vincularlo; no se auditaron commits remotos ni repositorios ajenos.

**Alcance:** no se detectaron secretos reales ni rutas personales en los candidatos inspeccionados tras revisar las coincidencias. La búsqueda es heurística y no equivale a una garantía universal ni a un escaneo de historial. La carpeta de trabajo actual no tiene `.git`; no se creó un repositorio en la raíz ni se modificó historial.

La revisión de la fase 6.3 identificó **47 archivos candidatos**, verificó **15 casos de inclusión/exclusión** y comprobó **85 enlaces locales**, incluidos sus anclajes cuando correspondía. Sus cuatro destinos de captura ausentes se reemplazaron en la fase 6.4 por las imágenes reales verificadas de `powerbi/screenshots/`. En la fase 6.3 se conservaron 22 archivos protegidos sin cambios; las excepciones de aquella instantánea fueron únicamente los dos notebooks reejecutados y el ajuste editorial indicado del diccionario. Las versiones originales del README y del diccionario se conservaron en la auditoría local excluida.

La fase 6.5 completó la revisión de `data_quality.md`, `sql_exploration.md`, `sql_advanced_analysis.md` y `sql_load_report.md`. Las claves de registros y los códigos de proyecto mostrados se contrastaron con el dataset público local. No se identificaron valores que requieran enmascaramiento adicional en esos cuatro informes. Se conservaron íntegros como evidencia y para mantener la conciliación automática; el inventario y los límites se detallan a continuación.

## Revisión final de seguridad y licencia — Fase 6.5

### Informes históricos y procedencia

Se revisaron los cuatro archivos completos, sus tablas y los campos de identificación potencial. La [ficha pública de Help Desk Tickets, versión 3](https://data.mendeley.com/datasets/btm76zndnt/3), consultada el 16/11/2026, confirma la publicación de los datos enmascarados. El [diccionario local del proveedor](../data/FEATURES.md#data-masking) especifica los campos marcados con `#`: proyectos, usuarios y valores de cambios de responsable. No se descargaron ni modificaron CSV.

| Informe | Campos o valores identificables revisados | Contraste real y decisión |
|---|---|---|
| [data_quality.md](data_quality.md) | `id` de ticket y evento; número de fila lógica CSV (`dq_source_row`); nombres de columnas de usuarios y sus conteos de nulos | 10 pares fila/ID de tickets y 1 par fila/ID de evento coinciden con los originales. La fila lógica es trazabilidad generada por el proyecto. Los nombres `issue_reporter`/`issue_assignee` describen el esquema: no se muestran sus valores. Conservar sin cambios |
| [sql_exploration.md](sql_exploration.md) | `proyecto` del top 10; campos `id`, `issueid`, `issue_num`, `change_group_id`, `value`, usuarios y `__raw` en el catálogo; rangos de procedencia y fechas | Los 10 códigos y sus conteos coinciden con `issue_proj` del CSV original. El proveedor documenta su enmascaramiento. El catálogo publica nombres/tipos de columnas, no valores de usuarios o de asignaciones. Fechas y rangos de esta parte son agregados. Conservar sin cambios |
| [sql_advanced_analysis.md](sql_advanced_analysis.md) | `id` en 20 discrepancias de reapertura y 10 intervalos extensos; fechas `creacion_utc`/`resolucion_utc`, prioridad, tipo, duraciones y flags por ticket | Las 30 referencias corresponden al CSV público. Se comprobaron conteos de eventos/reaperturas, fechas, dimensiones y duración de workflow mostrados. No aparecen nombres ni valores de responsables. Conservar las muestras, fechas y resultados sin cambios |
| [sql_load_report.md](sql_load_report.md) | `ID ticket` en 3 ejemplos; fecha `started`, duraciones decimales; nombres de campos identificadores/usuarios/`__raw` y hashes | Los 3 ejemplos coinciden con el original y con la representación CSV/SQL registrada. Los hashes son huellas de archivos, no tokens. Los conteos por columna no muestran identidades. Conservar sin cambios |

**Resultado de procedencia:** 43 referencias de tickets, 1 referencia de evento y 10 códigos de proyecto contrastados. Son referencias, no un nuevo conteo de tickets únicos. Los IDs técnicos se conservan tal como se publicaron: no se afirma que el proveedor los haya enmascarado. Los códigos de proyecto sí están documentados como enmascarados por el proveedor.

**Enmascaramiento adicional:** no se identificó ninguno necesario para los valores efectivamente mostrados en estos cuatro informes. Los IDs y las fechas por registro siguen siendo enlazables con la fuente pública y no constituyen anonimización irreversible. No se resolvieron ni intentaron resolver identidades originales. Los valores de usuarios (`issue_reporter`, `issue_assignee`, `value` cuando `field=assignee`), textos libres, datos de conexión y credenciales locales no se incorporan a esta documentación; los CSV y el PBIX siguen excluidos. Una futura incorporación de esos valores necesitaría una nueva revisión.

### Archivos candidatos a commit

Se enumeraron **52 candidatos**, incluido el nuevo `LICENSE`, con `git ls-files --others --exclude-standard` y las reglas anidadas reales. Se reutilizaron los metadatos auxiliares preexistentes de la auditoría, dentro de `.venv` y excluidos, indicando el árbol de trabajo explícitamente. **No se ejecutó `git init` ni se creó `.git` en la raíz.** El manifiesto, los resultados y las herramientas de esta auditoría permanecen en `.venv/security_license_audit/`; no contienen contraseñas ni se incluyen entre los candidatos.

| Control | Resultado real |
|---|---|
| Credenciales, contraseñas y tokens | Sin secretos reales detectados tras revisar las coincidencias; patrones de claves de proveedores, JWT, claves privadas, contraseñas literales y URLs con autenticación revisados |
| Contraste con la configuración local | Se compararon en memoria los valores secretos y de conexión, sin imprimirlos ni guardarlos en los artefactos de auditoría. Las coincidencias fueron identificadores de variables de pruebas, ejemplos de dirección local, una referencia al entorno y un literal sintético del test de escape |
| Rutas personales y correos | Sin coincidencias en candidatos, fuentes, metadatos o salidas textuales/HTML de notebooks. La configuración de VS Code usa una ruta relativa |
| Plantilla `.env.example` | `SQL_USER` y `SQL_PASSWORD` vacíos; sin valores reales de autenticación |
| Exclusiones | **25 de 25 controles superados**: secretos, CSV, PBIX, cachés y auditoría local excluidos; documentación, capturas y `LICENSE` permitidos. Los futuros `.kin/config`, `.kin/index.json` y `.kin/code-map.json` no se excluyen como caché |
| Temporales y binarios innecesarios | Ningún candidato con extensión temporal, backup, log, datos locales, archivo comprimido, base de datos, certificado o PBIX. Los auxiliares de revisión están excluidos |
| Tamaño | Ningún candidato supera el umbral de revisión de **5 MiB**. Los mayores son los notebooks: 652.956 y 420.057 bytes; se conservan sus salidas verificadas |
| Notebooks | Formato y fuentes comprobados; salidas almacenadas con 24 y 47 controles, 0 errores y 0 `stderr`. No aparecen columnas individuales de usuarios, proyectos o IDs en sus tablas HTML. Se revisaron metadatos de sus 4 y 7 PNG embebidos; no se reejecutaron ni modificaron |
| Capturas Power BI | Cuatro PNG válidos, sin metadatos adicionales; revisión visual repetida. Sin nombres personales, correos, rutas del equipo ni conexión visibles. Calidad de Datos conserva IDs técnicos y proyectos enmascarados del dataset, según la revisión de fase 6.4 |
| Informes y resultados | Cuatro informes revisados y conservados byte por byte; sin cambios en estadísticas, conteos, muestras ni precisión |

El escaneo cubre los 52 candidatos actuales; no certifica un staging o historial todavía inexistentes. La búsqueda de secretos es heurística y las imágenes se revisaron con el alcance indicado, sin afirmar que un patrón automático reconozca toda información posible.

### Licencia y titular confirmado

No se encontró un titular de copyright declarado en la configuración del proyecto: `.vscode/settings.json` configura únicamente Python, no hay manifiesto de autoría y `.kin/config` no existe. Tampoco hay campos de autoría en la configuración local. No se tomó el nombre del usuario del sistema ni del proveedor de datos como prueba de titularidad. Se solicitó el dato y el usuario confirmó expresamente **Daniel Prado Jimenez**.

Se creó [LICENSE](../LICENSE) con el texto MIT y **Copyright (c) 2026 Daniel Prado Jimenez**. El texto se contrastó con la [licencia MIT publicada por Open Source Initiative](https://opensource.org/license/mit). El README aplica MIT al código propio Python/SQL y a las celdas de código propias de los notebooks; conserva la atribución del material del proveedor y de los extractos del dataset bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). El dataset no se relicencia bajo MIT.

### Integridad y preparación

Las huellas SHA-256 se compararon con una instantánea tomada antes de editar: **56 archivos protegidos permanecen idénticos**, incluidos los cuatro informes históricos, CSV, SQL, código, tests, notebooks, capturas, PBIX y configuración local. Los cambios del proyecto son únicamente `README.md`, este checklist y el nuevo `LICENSE`. Las bases de memoria se preservaron; no se regeneraron snapshots de Kindex.

La validación final comprobó además **83 enlaces locales de Markdown y 11 anclajes**, sin destinos ausentes, y confirmó que los campos de autenticación de `.env.example` permanecen vacíos. Los 52 candidatos no tienen hallazgos de seguridad sin resolver; `.git` sigue ausente en la raíz.

La fase 6.5 no se conectó a SQL Server ni ejecutó cargadores, consultas o pruebas SQL. Se conserva como evidencia la reverificación anterior de 4/4 pruebas y los conteos **66.691 tickets, 257.508 eventos y 1.333.820 filas de estados**. La comprobación local de procedencia volvió a leer los CSV originales, sin escribirlos.

**Preparado para inicializar Git:** sí, para los archivos actuales y el alcance revisado. No quedan pendientes de licencia ni de revisión de granularidad de los cuatro informes. Quedan los controles de una fase posterior: revisar el staging real antes del primer commit, preservar/revisar cualquier historial externo que se quiera vincular y obtener autorización para publicar. Esta conclusión no ejecuta ni autoriza por sí sola esos pasos.

## Licencia y atribución

- [x] Autor, título, versión 3 y DOI `10.17632/btm76zndnt.3` documentados.
- [x] Licencia **CC BY 4.0 del dataset** confirmada en [la ficha de Mendeley Data](https://data.mendeley.com/datasets/btm76zndnt/3), consultada el 15 de noviembre de 2026.
- [x] Crédito, enlace a [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) e indicación de transformaciones incluidos en README.
- [x] Diccionario `FEATURES.md` del proveedor atribuido, con su ajuste editorial explícito: enlace al diagrama ausente dirigido a la fuente original; sin cambiar definiciones de campos.
- [x] Diferenciada la licencia del dataset de la licencia del código propio.
- [x] Licencia MIT elegida expresamente por el usuario; titular confirmado: Daniel Prado Jimenez. `LICENSE` creado con año 2026; alcance diferenciado en README.

La ficha web actual describe datos desde 2007, mientras el diccionario local indica tickets desde 2016. Ambas referencias y los extremos observados están explicados en el README. No se modificaron las fuentes ni los informes históricos para ocultar esa diferencia.

## Archivos candidatos y tratamiento

| Grupo | Tratamiento |
|---|---|
| `src/*.py`, `sql/*.sql`, `tests/*.py`, dependencias | Publicables tras la revisión de staging; los literales de pruebas son ficticios |
| `README.md`, `notebooks/README.md`, informe final y checklist | Publicables; capturas integradas y reverificación SQL registrada en este checklist |
| Ambos `.ipynb` | Publicables con las salidas revisadas y contadores consecutivos |
| `data/FEATURES.md` | Publicable como documentación atribuida del dataset, sin CSV |
| Diccionarios/modelos e informes históricos | Granularidad revisada en fase 6.5; cuatro informes conservados como evidencia pública, con claves técnicas y códigos de proyecto enmascarados documentados |
| `LICENSE` | MIT para el código propio; copyright 2026 Daniel Prado Jimenez; dataset y material del proveedor bajo CC BY 4.0 |
| `.env.example`, `.gitignore`, `.kin/.gitignore` | Publicables; no contienen valores reales de autenticación |
| `.vscode/settings.json` | Opcional y revisado: intérprete relativo a `.venv`, sin ruta personal; otros archivos de VS Code quedan excluidos |
| `.kin/config`, `.kin/index.json`, `.kin/code-map.json` si se crean | No existen actualmente; aplicar el contrato de memoria y revisar antes de incluir; no excluirlos como caché por defecto |
| `data/raw/`, `data/processed/`, demás datos locales | Excluir, excepto marcadores `.gitkeep` y el diccionario permitido |
| `.env`, `.venv/`, `.kin/local/`, credenciales y bases locales | Excluir y preservar localmente; no son archivos de portafolio |
| `powerbi/HelpDesk_Analytics.pbix` | Excluir: conserva datos importados y configuración local |
| `powerbi/screenshots/*.png` | Cuatro capturas reales revisadas e integradas; Calidad de Datos incluye el detalle enmascarado documentado |

## Inicialización y revisión del staging — Fase 6.6

La raíz confirmada es `analisis-datos`. Antes de iniciar no había `.git` en la raíz ni un repositorio Git en sus directorios superiores. Se ejecutó `git init --initial-branch=main .`; no se reutilizó ni sobrescribió configuración existente. Se conservó la configuración heredada, incluido `core.autocrlf=true`, y no se configuraron remotos ni identidad de autor. No se creó ningún commit.

### Exclusiones y ajustes previos

Se revisaron `.gitignore` y `.kin/.gitignore`. Las exclusiones existentes protegen `.env`, entornos virtuales, credenciales, cachés, CSV, PBIX y bases de datos locales. Se añadieron patrones para temporales, copias de respaldo, restos de editores/merges y archivos auxiliares de bases SQLite (`*.tmp`, `*.temp`, `*.bak`, `*.swp`, `*.swo`, `*~`, `*.orig`, `*.rej`, `*.sqlite3`, `*.sqlite-*`, `*.sqlite3-*`, `*.db-*`). Se preservan los futuros artefactos compartibles `.kin/config`, `.kin/index.json` y `.kin/code-map.json`; actualmente no existen.

Se retiraron únicamente espacios finales de **8 líneas**: 3 en `data/FEATURES.md`, 1 en `reports/final_analysis.md` y 4 líneas vacías en `sql/04_advanced_analysis.sql`. El texto y los tokens permanecen iguales al ignorar ese espacio. No cambian definiciones, consultas, resultados, conteos ni métricas. Los originales se conservaron en la auditoría local excluida. README y este checklist reflejan el estado actual de Git.

### Selección y revisión del índice

Se agregaron mediante una lista explícita los **52 archivos** de la revisión anterior, sin `git add -f`. La lista incluye `requirements-dev.txt` y la configuración relativa de Python en `.vscode/settings.json`, necesarios para reproducibilidad; no contiene preferencias personales ni secretos. Los marcadores `.gitkeep` conservan directorios vacíos. `.env.example` mantiene vacíos los campos de autenticación.

Se ejecutaron `git status`, `git diff --cached --stat`, `git diff --cached --name-only` y `git diff --cached --check`. La revisión de seguridad leyó los blobs del índice, no solo las copias del árbol de trabajo: claves de proveedores, JWT, contraseñas, URLs con autenticación, claves privadas, rutas personales, correos, salidas y metadatos de notebooks y metadatos PNG. Se contrastaron en memoria los valores locales sin mostrarlos ni guardarlos. Las coincidencias conocidas son ejemplos locales, referencias al entorno, identificadores de tests y un literal sintético; no hay hallazgos de seguridad sin resolver.

Las cuatro capturas y ambos notebooks corresponden a los archivos revisados en fase 6.5; se conservaron sus huellas. El índice coincide con el árbol de trabajo después de la normalización de finales de línea configurada por Git. Ningún archivo ignorado ni archivo indebido aparece preparado. `git diff --cached --check` termina con código 0. No quedan cambios adicionales de archivos candidatos fuera del staging.

El contenido preparado ocupa aproximadamente **1,9 MiB**, calculado a partir de los blobs del índice, sin incluir `.git`, los datos locales o el entorno virtual. Ningún archivo preparado supera 5 MiB. El inventario exacto es:

```text
.env.example
.gitignore
.kin/.gitignore
.vscode/settings.json
LICENSE
README.md
data/FEATURES.md
data/processed/.gitkeep
data/raw/.gitkeep
notebooks/.gitkeep
notebooks/01_exploratory_analysis.ipynb
notebooks/02_advanced_analysis.ipynb
notebooks/README.md
powerbi/.gitkeep
powerbi/model_setup.md
powerbi/screenshots/01_resumen_general.png
powerbi/screenshots/02_analisis_operativo.png
powerbi/screenshots/03_tiempos_por_estado.png
powerbi/screenshots/04_calidad_datos.png
reports/bi_data_model.md
reports/bi_data_model_design.md
reports/data_quality.md
reports/figures/.gitkeep
reports/final_analysis.md
reports/publication_checklist.md
reports/sql_advanced_analysis.md
reports/sql_environment.md
reports/sql_exploration.md
reports/sql_load_report.md
reports/sql_schema.md
requirements-dev.txt
requirements.txt
sql/.gitkeep
sql/01_create_database.sql
sql/02_create_tables.sql
sql/03_exploratory_analysis.sql
sql/04_advanced_analysis.sql
sql/05_bi_views.sql
src/advanced_sql.py
src/bi_views.py
src/clean_data.py
src/explore_sql.py
src/inspect_data.py
src/load_to_sql.py
src/prepare_sql_schema.py
src/sql_connection.py
tests/.gitkeep
tests/test_bi_views.py
tests/test_bi_views_integration.py
tests/test_clean_data.py
tests/test_load_to_sql.py
tests/test_sql_schema.py
```

**Excluidos y conservados localmente:** `.env`, `.venv/` y sus auditorías, cachés Python/Jupyter, todos los CSV originales/procesados, `data/EXAMPLE.md`, `powerbi/HelpDesk_Analytics.pbix`, bases `.kin/local/` y demás bases/credenciales/temporales cubiertos por las reglas. No se borraron archivos ni bases de memoria. No se conectó a SQL Server ni se modificaron datos o métricas.

**Resultado:** el primer commit está preparado para aprobación. La inicialización, las ocho correcciones de espacio y la revisión del índice no dejan problemas pendientes. Esta fase termina antes de crear el commit o vincular un remoto.

## Pendientes reales antes de publicar

1. Obtener aprobación para crear el primer commit con el staging revisado de fase 6.6. Si se modifica el índice o algún archivo preparado, volver a revisar el contenido antes de confirmar.
2. Si se pretende vincular otro historial o un remoto, preservarlo y revisarlo antes; no se auditaron repositorios ajenos en esta fase.
3. Obtener autorización para publicar o hacer push. **Esta fase no incluye publicación, push ni inicialización de Git.**
