# Notebooks de HelpDesk Analytics

[01_exploratory_analysis.ipynb](01_exploratory_analysis.ipynb) presenta el análisis exploratorio de tickets y eventos procesados. Incluye diez secciones, tablas pequeñas y cuatro gráficos: prioridades, resoluciones, creaciones anuales y creaciones mensuales. Las interpretaciones y los controles están dentro del notebook.

[02_advanced_analysis.ipynb](02_advanced_analysis.ipynb) desarrolla nueve secciones de análisis avanzado: tiempos calendario, sensibilidad temporal, cohortes, prioridad y tipo, reaperturas, estados, calidad y conclusiones. Contiene **42 celdas: 22 Markdown y 20 Python**, con **siete figuras**. Ambos notebooks son independientes y utilizan el mismo entorno y paleta visual; no es necesario ejecutar el primero para utilizar el segundo.

## Preparación del entorno

Desde la raíz del proyecto, en PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --sys-prefix --name helpdesk-analytics --display-name "Python (.venv HelpDesk Analytics)"
```

Si todavía no existe el entorno, créalo primero con `python -m venv .venv`. El kernel se registra dentro de `.venv`, que está excluido de Git. No requiere registrar rutas personales en el notebook ni instalar un servidor Jupyter Notebook o JupyterLab. En Linux/macOS, sustituye los ejecutables de `.venv\Scripts\` por sus equivalentes en `.venv/bin/`.

Dependencias específicas: `ipykernel` ejecuta Python como kernel; `nbformat` permite validar el archivo; `nbclient` permite ejecutar todas sus celdas sin interfaz gráfica. Pandas, NumPy y Matplotlib ya forman parte del proyecto. Los rangos de `requirements.txt` no son un bloqueo exacto del entorno; las versiones usadas se muestran en la segunda sección del notebook.

## Abrir y ejecutar en VS Code

1. Abre la carpeta raíz del proyecto en VS Code y comprueba que estén habilitadas las extensiones **Python** y **Jupyter** de Microsoft.
2. Abre `notebooks/01_exploratory_analysis.ipynb` o `notebooks/02_advanced_analysis.ipynb`.
3. En **Seleccionar kernel / Select Kernel**, elige **Python (.venv HelpDesk Analytics)** o el entorno Python `.venv` de este proyecto. Si aparecen varios entornos, utiliza el ejecutable de `.venv`, no el Python global.
4. Utiliza **Reiniciar kernel / Restart Kernel** y después **Ejecutar todo / Run All** para comprobar la ejecución desde cero.
5. Guarda el archivo para conservar las salidas. Las tablas de validación deben mostrar **SUPERADA**: el primero contiene cuatro figuras y el segundo, siete.

La configuración del workspace propone `.venv` como intérprete predeterminado. El notebook comprueba por separado que el kernel activo corresponde a ese entorno y busca la raíz del proyecto recorriendo los directorios superiores. Puede arrancar con directorio de trabajo en la raíz o en `notebooks/`.

## Ejecutar sin interfaz

Desde la raíz, después de registrar el kernel:

```powershell
$env:PYTHONUTF8 = '1'
$env:JUPYTER_CONFIG_DIR = Join-Path (Get-Location) '.venv/jupyter/config'
$env:JUPYTER_RUNTIME_DIR = Join-Path (Get-Location) '.venv/jupyter/runtime'
$env:IPYTHONDIR = Join-Path (Get-Location) '.venv/ipython'
$env:MPLCONFIGDIR = Join-Path (Get-Location) '.venv/matplotlib'
.\.venv\Scripts\jupyter.exe execute notebooks/01_exploratory_analysis.ipynb --kernel_name=helpdesk-analytics --timeout=180 --inplace
.\.venv\Scripts\jupyter.exe execute notebooks/02_advanced_analysis.ipynb --kernel_name=helpdesk-analytics --timeout=180 --inplace
```

`PYTHONUTF8=1` evita que el ejecutor de notebooks interprete el archivo UTF-8 con otra codificación de Windows. Las otras variables sitúan configuración, historial y cachés en `.venv`, sin escribir en carpetas globales del usuario. Son variables de la sesión de terminal; no se guardan credenciales ni rutas personales en el notebook.

`--inplace` guarda las salidas en el mismo notebook. No se permite continuar tras errores. La ejecución sólo lee los CSV y los informes; no conecta a SQL Server, no ejecuta la limpieza y no modifica Power BI. En un equipo nuevo deben estar disponibles previamente los datos procesados mediante el flujo del proyecto descrito en [README](../README.md).

Ejecuta sólo la línea del notebook que quieras reproducir. Para verificar el segundo desde `notebooks/`, conserva las variables anteriores, calculadas desde la raíz, y utiliza:

```powershell
Push-Location notebooks
..\.venv\Scripts\jupyter.exe execute 02_advanced_analysis.ipynb --kernel_name=helpdesk-analytics --timeout=180 --inplace
Pop-Location
```

## Datos, controles y publicación

Archivos necesarios:

- `data/processed/issues_clean.csv` y `data/processed/issues_change_history_clean.csv`.
- `reports/sql_exploration.md` y `reports/data_quality.md`, usados como referencia verificable del primero.
- `reports/sql_advanced_analysis.md`, referencia numérica del segundo; `reports/final_analysis.md` contrasta además las reaperturas por prioridad.
- `reports/final_analysis.md` y `data/FEATURES.md`, como documentación de contexto.

Los datos no se distribuyen en Git. El lector existente considera nulo sólo un campo vacío y preserva etiquetas como `unknown`; las conversiones para analizar se realizan únicamente en memoria. No se duplica el ETL dentro del notebook.

Se contrastan volúmenes, prioridades, resoluciones, los 17 años y los 192 meses observados, cobertura histórica, flags y ausencias documentadas. Un error de conciliación detiene la ejecución y exige investigar la discrepancia; no se ajustan cifras ni se actualizan informes para forzar coincidencias. El notebook verifica también las huellas de ambos CSV procesados antes y después de sus cálculos.

Las salidas guardadas contienen agregados y muestras de cinco filas de campos seleccionados. No se publican usuarios, proyectos, identificadores de tickets o eventos, valores de asignación, columnas `__raw`, rutas del equipo ni credenciales. Antes de subir futuras ejecuciones, revisa que no haya errores con trazas locales ni salidas ampliadas accidentalmente. Los PNG están embebidos para poder leer los gráficos en GitHub sin ejecutar Python.

La cobertura real comienza en 2007 para tickets y en 2015 para eventos, aunque la documentación del origen describe tickets desde 2016. Esta diferencia se conserva y explica; 2007 y 2023 son años parciales. `Done` es una resolución registrada, no una medida de satisfacción ni de cumplimiento de SLA.

## Validación del notebook 01

El 14 de noviembre de 2026 se ejecutaron las 23 celdas Python, en orden y con kernel nuevo, tanto desde `notebooks/` mediante el comando anterior como desde la raíz mediante `NotebookClient`. Se superaron 24 controles internos, incluidos los 17 años y los 192 meses de las tablas SQL, y se comprobaron los cuatro gráficos PNG embebidos. No se encontraron discrepancias numéricas.

La revisión final comprobó el formato del notebook, los enlaces locales y las salidas guardadas, sin errores ni trazas con rutas personales. Las huellas de 19 archivos protegidos —los cuatro CSV, los cinco scripts SQL, el PBIX y los nueve informes— permanecieron idénticas. No se establecieron conexiones a SQL Server. `pip check` no detectó incompatibilidades de dependencias.

Los problemas iniciales de lectura de acentos por la codificación de Windows y de permisos para escribir configuración e historial globales se resolvieron con las variables de la sección de ejecución sin interfaz. Las advertencias del lanzador del kernel no forman parte de las salidas publicadas; no impidieron ejecutar las celdas ni generar los gráficos.

## Análisis avanzado: gráficos y criterios

Las siete figuras del segundo notebook son:

1. Histogramas completos de tiempos calendario, en paneles separados para `Done` y otras resoluciones, con mediana y P90. Usan los mismos intervalos lineales, sin recortar extremos.
2. Comparación de mediana y P90 entre la población `Done` completa y las creaciones desde 2016; se incluyen sus tamaños elegibles y exclusiones.
3. Mediana y P90 por cohorte anual, con escala logarítmica y marcadores de años parciales. El cálculo y la conciliación también incluyen todas las cohortes mensuales.
4. Mediana y P90 por prioridad, manteniendo `unknown` y mostrando el número elegible. Los segmentos entre cuantiles no son intervalos de confianza.
5. Mapa de medianas por prioridad y tipo, con n por celda. Muestra los cinco tipos de mayor volumen, mientras se validan las 78 combinaciones observadas; `n < 30` es una señal editorial de atención, no significación estadística.
6. Comparación de volumen y proporción de tickets con reapertura por prioridad, con denominadores explícitos.
7. Dispersión de duración acumulada típica frente a tickets que recorrieron cada estado, en ejes logarítmicos. Los negativos se conservan en la auditoría y se identifican por color.

Los `wf_*` se transforman con `melt` a **1.333.820 parejas ticket–estado**. Se conserva la duración original como texto y una versión numérica analítica; las sumas se contrastan con `Decimal`, sin redondeo de auditoría. Se comprueban todas las parejas y valores de duración/visitas frente a la estructura ancha. Los cuantiles no negativos excluyen explícitamente nulos y negativos; se mantienen también cuantiles firmados y conteos separados.

El notebook utiliza agregaciones de Pandas para los resultados y los verifica con `Series.quantile` y `NumPy.quantile(method='linear')`. Los conteos y sumas decimales deben coincidir exactamente; los percentiles aproximados siguen la tolerancia documentada del proyecto: absoluta de 0,0001 en la unidad de salida y relativa de 10⁻¹². No se instalan dependencias adicionales a las del primer notebook.

## Resultados y validación del notebook 02

La ejecución conserva las nueve secciones solicitadas y registra **47 controles superados**. Se contrastan **12 tablas del informe SQL avanzado, con 364 filas de resultados**, incluidas las 209 cohortes anuales/mensuales, las siete prioridades, las 78 combinaciones prioridad–tipo, los 20 estados y los cinco escenarios de sensibilidad. La muestra SQL de discrepancias y los casos extremos se comprueban en memoria; sólo se publican resúmenes sin identificadores.

El 14 de noviembre de 2026 se ejecutó la versión final completa con kernel nuevo tanto desde la raíz como desde `notebooks/`. Se revisaron visualmente las siete figuras y se validó el formato con `nbformat`. Las salidas guardadas no contienen errores ni trazas de ejecución; la tabla más larga tiene 20 filas y el notebook ocupa aproximadamente 638 KiB. Las huellas SHA-256 de 22 archivos protegidos permanecieron idénticas, incluidos los CSV originales y procesados, scripts SQL, PBIX, informes, notebook 01, dependencias y configuración de VS Code. No se conectó a SQL Server ni se instalaron paquetes nuevos; `pip check` no detectó incompatibilidades.

Resultados principales calculados:

- `Done`, base completa: 62.034 elegibles; mediana **35,87 días calendario** y P90 **2.858,35 días**.
- `Done`, creaciones desde 2016: 38.747 elegibles y 23.287 excluidos de la base; mediana **9,08 días** y P90 **103,06 días**.
- Reaperturas: **2.123 tickets**, **2.364 visitas agregadas**, **2.325 eventos** y **39 tickets discrepantes** entre 66.650 comparables. De esos 39, 38 tienen más visitas agregadas y uno tiene más eventos: la diferencia neta es **39** y la suma absoluta, **41**. No son el mismo indicador.
- Calidad: **450 tickets señalados**, **55 con negativos** y **374 con discrepancia de duración**; **44** tienen ambas condiciones.
- Estados: `pending_deployment` tiene la mayor mediana no negativa, **12,00 días**, sobre 1.413 elegibles; `open` reúne la mayor suma positiva. Estos rankings no prueban cuellos de botella ni miden horas trabajadas.

La comparación por prioridad, las cohortes y los filtros de calidad no identifican efectos causales. Las cohortes recientes pueden estar censuradas y los registros antiguos requieren aclaración de semántica; los escenarios se muestran junto a la base, sin eliminar casos automáticamente. `Done` no se interpreta como satisfacción. Las recomendaciones se relacionan con las cuatro páginas de Power BI, sin modificar el dashboard ni certificar sus medidas DAX.

No se encontraron discrepancias numéricas entre los cálculos de esta entrega y las referencias contrastadas. Esto no elimina las discrepancias del origen: los 39 casos de reapertura y las anomalías señaladas siguen presentes. También permanece la diferencia entre la cobertura descrita desde 2016 y las creaciones observadas desde 2007, así como la cobertura de eventos desde 2015. Las advertencias del lanzador de Jupyter no afectaron las ejecuciones ni se conservaron en las salidas publicadas.

## Integración para publicación · 15 de noviembre de 2026

Se revisaron ambos notebooks y se detectaron contadores de ejecuciones parciales posteriores a las entregas anteriores. Se reejecutaron las celdas actuales desde la raíz con kernels nuevos y se guardaron contadores consecutivos. **No se modificaron el código, las celdas Markdown ni sus identificadores**; se comprobó que todas las salidas textuales y tablas siguieran siendo idénticas. Los controles continúan en 24 y 47 y las figuras, en cuatro y siete.

La revisión de fuentes, metadatos, tablas, salidas y metadatos de PNG no detectó rutas personales, credenciales ni trazas de error en los notebooks publicados. Las tablas más largas contienen 17 y 20 filas. Los CSV procesados y las referencias originales permanecieron intactos; no se conectó a SQL Server desde los notebooks.

`data/FEATURES.md` queda permitido explícitamente por `.gitignore`, porque es documentación pública del proveedor necesaria para las comprobaciones de carga y sus enlaces. Los CSV y el resto de datos locales siguen excluidos. La licencia y atribución del dataset están en [README](../README.md#fuente-de-datos-y-atribución).

La auditoría general, el alcance de la búsqueda de secretos, las pruebas y los pendientes se registran en [el checklist de publicación](../reports/publication_checklist.md). En particular, la validación actual contra SQL Server requiere repetir la integración desde un entorno con acceso: el intento de esta fase terminó con SQLSTATE 08001 en la conexión, antes de ejecutar sus cuatro pruebas.
