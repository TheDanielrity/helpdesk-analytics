# Configuración manual del modelo Power BI — Fase 4.1

## Alcance y estado de la evidencia

Esta guía documenta pasos **pendientes de comprobar manualmente en Power BI Desktop**. Se basa en el diccionario y las verificaciones SQL de [bi_data_model.md](../reports/bi_data_model.md), Fase 3.6. No se abrió ni controló la interfaz de Desktop, no se inspeccionó el modelo del PBIX, no se configuraron relaciones y no se crearon medidas DAX en esta fase. Tampoco se ejecutó DDL ni se modificaron registros, vistas o CSV.

Ruta de trabajo prevista: **`powerbi/HelpDesk_Analytics.pbix`**. Durante esta revisión ya existe un archivo con ese nombre; se conservó sin cambios y su configuración interna **no está verificada**. Si se continúa sobre él, comprobar primero los pasos siguientes y guardar una copia local antes de editar. El patrón `*.pbix` ya está excluido en `.gitignore`; su existencia no implica publicación ni versionado.

## 1. Conexión mediante Importar

1. Abrir Power BI Desktop manualmente y abrir el archivo de trabajo, o iniciar un archivo nuevo si corresponde. Revisar si ya hay consultas antes de agregar otras: no duplicar las fuentes existentes.
2. Inicio → Obtener datos → SQL Server (o Base de datos de SQL Server, según versión).
3. Escribir la instancia SQL Server utilizada localmente y la base **HelpDeskAnalytics**. No pegar cadenas que incluyan usuario/contraseña ni copiar el contenido de `.env` en una consulta.
4. Seleccionar **Importar**, no DirectQuery. No introducir instrucciones SQL en Opciones avanzadas para esta carga: navegar directamente hasta las vistas.
5. En el diálogo de autenticación, elegir **Base de datos**, introducir las credenciales SQL locales autorizadas y conectar. Las credenciales del entorno Python no configuran Desktop automáticamente. Si hubiera credenciales previas incorrectas, revisar Archivo → Opciones y configuración → Configuración de origen de datos y editar los permisos del origen correspondiente, sin escribir contraseñas en documentación o código.
6. Si aparece un error de certificado, resolver la confianza del certificado de ese servidor en el cliente siguiendo la documentación del conector. `SQL_TRUST_SERVER_CERTIFICATE=yes` de pyodbc no se transfiere a Desktop. No interpretar una conexión Python exitosa como prueba de conectividad de Desktop.
7. En Navegador, seleccionar **sólo** `bi.vw_tickets`, `bi.vw_ticket_events` y `bi.vw_ticket_state_durations`. No cargar las tablas stg ni agregar una segunda copia de las vistas.
8. Elegir **Transformar datos** y utilizar estos nombres de consulta para que las instrucciones posteriores coincidan: `vw_tickets`, `vw_ticket_events`, `vw_ticket_state_durations`.
9. Comprobar Origen y Navegación en Pasos aplicados: mismo servidor/base, esquema bi y vista correcta. Verificar que no haya filtros de año, eliminación de errores, sustitución de NULL, eliminación de negativos o deduplicación de datos heredados de una configuración previa. No corregir los conteos mediante esos pasos.
10. Aplicar los tipos de la sección 2, revisar las validaciones y después **Cerrar y aplicar**. Confirmar que las tres tablas quedan en modo Importar. Actualizar recupera una nueva copia de las vistas; los cambios SQL no aparecen en el PBIX hasta actualizar.

Referencia del flujo de conexión y autenticación: [conector SQL Server de Microsoft](https://learn.microsoft.com/en-us/power-query/connectors/sql-server). Los nombres de menús pueden variar entre versiones.

## 2. Tipos y propiedades por columna

Las tablas siguientes incluyen **cada columna** del diccionario SQL de Fase 3.6. Revisar tanto el tipo en Power Query como el tipo del modelo, sin confiar exclusivamente en la inferencia automática. No cambiar los tipos de SQL para adaptar el PBIX. La nulabilidad detallada y las definiciones de negocio permanecen en [bi_data_model.md](../reports/bi_data_model.md).

| Tipo SQL | Power Query / modelo | Regla |
|---|---|---|
| BIGINT / INT | Número entero | IDs, año, mes y procedencia: No resumir. Los conteos sólo se suman cuando se respeta su granularidad |
| BIT | Verdadero/Falso | Preservar NULL si existe; no reemplazarlo por False |
| NVARCHAR | Texto | Preservar etiquetas, espacios originales de auditoría, unknown y NULL; nunca convertir __raw a número/fecha |
| DATE | Fecha | No agregar componente horario ni desplazamiento de zona |
| DATETIME2(7) | Fecha/hora | Instante ya normalizado a UTC; no convertir a hora local ni volver a asignar un desplazamiento |
| DECIMAL / FLOAT | Número decimal | Aproximado en el modelo; no elegir Número decimal fijo por defecto ni interpretar formato visual como precisión almacenada |

**No resumir es el valor inicial recomendado para las columnas numéricas analíticas**, hasta definir medidas en una fase posterior. Esto evita que Desktop sume automáticamente duraciones, IDs o años. No crea métricas DAX. Las fechas pueden mostrarse con formato `yyyy-MM-dd HH:mm:ss` y las fechas DATE con `yyyy-MM-dd`; el formato no cambia el instante ni garantiza precisión de microsegundos en el modelo.

### vw_tickets

| Columna | Tipo SQL de referencia | Tipo Power Query / modelo | Propiedad inicial |
|---|---|---|---|
| ticket_id | BIGINT | Número entero | No resumir |
| proyecto | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| tipo | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| prioridad | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| estado | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| resolucion | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| creacion_utc | DATETIME2(7) | Fecha/hora (UTC por convención) | Sin desplazamiento local |
| resolucion_utc | DATETIME2(7) | Fecha/hora (UTC por convención) | Sin desplazamiento local |
| fecha_creacion_utc | DATE | Fecha | Sin hora |
| anio_creacion | INT | Número entero | No resumir |
| mes_creacion | INT | Número entero | No resumir |
| periodo_creacion | DATE | Fecha | Sin hora |
| intervalo_calendario_segundos | DECIMAL(28,7) | Número decimal | No resumir; revisar precisión |
| tiempo_calendario_segundos | DECIMAL(28,7) | Número decimal | No resumir; revisar precisión |
| tiempo_calendario_dias | DECIMAL(28,12) | Número decimal | No resumir; revisar precisión |
| elegible_calendario | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| elegible_done | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| elegible_otra_resolucion | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| motivo_elegibilidad | NVARCHAR(32) | Texto | Sin conversión ni sustitución |
| cantidad_eventos | BIGINT | Número entero | No resumir |
| eventos_reopened | BIGINT | Número entero | No resumir |
| eventos_assignee | BIGINT | Número entero | No resumir |
| tiene_historial | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| inicio_historial_observado_utc | DATETIME2(7) | Fecha/hora (UTC por convención) | Sin desplazamiento local |
| creacion_anterior_inicio_historial | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| cobertura_historica | NVARCHAR(50) | Texto | Sin conversión ni sustitución |
| visitas_reopened_agregadas | BIGINT | Número entero | No resumir |
| reaperturas_comparables | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| diferencia_reopened | BIGINT | Número entero | No resumir |
| wf_total_time_segundos | DECIMAL(38,16) | Número decimal | No resumir; revisar precisión |
| dq_source_row | BIGINT | Número entero | No resumir |
| dq_duplicate_row | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_issue_num | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_issue_num | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_duplicate_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_started | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_started | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_naive_started | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_ended | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_ended | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_naive_ended | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_issue_created | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_issue_created | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_naive_issue_created | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_issue_resolution_date | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_issue_resolution_date | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_naive_issue_resolution_date | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_last_change_date | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_last_change_date | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_naive_last_change_date | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_optional | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_invalid_duration | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_negative_workflow_duration | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_negative_elapsed | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_negative_duration | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_duration_comparable | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_duration_mismatch | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_resolution_before_creation | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_last_change_before_creation | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_start_before_creation | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_end_after_last_change | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_duplicate_project_number | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_no_history | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_has_problem | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |

### vw_ticket_events

| Columna | Tipo SQL de referencia | Tipo Power Query / modelo | Propiedad inicial |
|---|---|---|---|
| event_id | BIGINT | Número entero | No resumir |
| ticket_id | BIGINT | Número entero | No resumir |
| campo | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| valor | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| evento_utc | DATETIME2(7) | Fecha/hora (UTC por convención) | Sin desplazamiento local |
| fecha_evento_utc | DATE | Fecha | Sin hora |
| grupo_cambio_id | BIGINT | Número entero | No resumir |
| dq_source_row | BIGINT | Número entero | No resumir |
| dq_duplicate_row | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| id__raw | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| dq_invalid_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| issueid__raw | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| dq_invalid_issueid | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_issueid | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| change_group_id__raw | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| dq_invalid_change_group_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_change_group_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_duplicate_id | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| created__raw | NVARCHAR(256) | Texto | Sin conversión ni sustitución |
| dq_invalid_created | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_created | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_naive_created | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_missing_optional | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_orphan_issue | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_parent_ambiguous | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_event_before_creation | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_event_after_last_change | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| dq_has_problem | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |

### vw_ticket_state_durations

| Columna | Tipo SQL de referencia | Tipo Power Query / modelo | Propiedad inicial |
|---|---|---|---|
| ticket_id | BIGINT | Número entero | No resumir |
| estado | NVARCHAR(25) | Texto | Sin conversión ni sustitución |
| duracion_segundos | DECIMAL(38,16) | Número decimal | No resumir; revisar precisión |
| numero_visitas | BIGINT | Número entero | No resumir |
| duracion_segundos_exacta | NVARCHAR(50) | Texto | Sin conversión ni sustitución |
| indicador_duracion_negativa | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| duracion_faltante | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| duracion_cero | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| estado_no_recorrido | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| estado_recorrido | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| elegible_duracion_no_negativa | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| elegible_promedio_visita | BIT | Verdadero/Falso | Conservar NULL; no convertir a 0/1 |
| promedio_por_visita_segundos | FLOAT | Número decimal | No resumir; revisar precisión |


## 3. Relaciones del modelo

Crear manualmente y verificar en Modelado/Administrar relaciones:

| Lado único (1) | Lado múltiple (*) | Activa | Dirección de filtro |
|---|---|---|---|
| vw_tickets[ticket_id] | vw_ticket_events[ticket_id] | Sí | Única: tickets → eventos |
| vw_tickets[ticket_id] | vw_ticket_state_durations[ticket_id] | Sí | Única: tickets → estados |

Los tres ticket_id deben ser **Número entero**. Desktop puede mostrar el diálogo en orden inverso (*:1); confirmar que el lado único sigue siendo vw_tickets y que la flecha parte de tickets. No aceptar muchos-a-muchos si la relación 1:* falla: investigar claves o tipos. La detección automática no sustituye estas comprobaciones.

```text
vw_tickets (1) ──→ (*) vw_ticket_events
              └─→ (*) vw_ticket_state_durations
```

- vw_tickets: clave ticket_id, una fila por ticket.
- vw_ticket_events: clave event_id. ticket_id se repite legítimamente.
- vw_ticket_state_durations: clave lógica compuesta (ticket_id, estado). ticket_id se repite **20 veces** por diseño. La relación usa sólo ticket_id porque el lado único es tickets; no crear una clave concatenada ni una relación estado→estado final.
- No relacionar eventos con estados ni activar filtrado en ambas direcciones. No combinar las tres consultas en una tabla plana.
- Usar proyecto, tipo, prioridad, estado final, resolución, año/mes y calidad de tickets como filtros compartidos. Un filtro propio de eventos o de estados no debe regresar automáticamente a tickets ni propagarse hacia la otra hija.
- Si ya hay otras relaciones automáticas, revisarlas antes de dar el modelo por válido; eliminar sólo relaciones de modelo redundantes tras comprobar su función, sin cambiar vistas SQL. No añadir todavía calendario ni relaciones adicionales de fechas. En una fase futura habrá que evitar dos rutas activas desde un mismo calendario hacia eventos.

Referencia: [relaciones de modelo en Power BI](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand).

## 4. Comprobación de conteos sin DAX

Los siguientes son **valores de referencia verificados en SQL en Fase 3.6**, no resultados medidos en Desktop durante esta fase:

| Consulta | Filas esperadas sin filtros | Clave y comprobación |
|---|---:|---|
| vw_tickets | 66.691 | ticket_id sin NULL; 66.691 valores distintos |
| vw_ticket_events | 257.508 | event_id sin NULL; 257.508 distintos; ticket_id debe existir en tickets |
| vw_ticket_state_durations | 1.333.820 | 20 estados por ticket; 1.333.820 parejas distintas (ticket_id, estado); ticket_id debe existir en tickets |

### A. Contar el conjunto completo en Power Query

La vista previa suele mostrar una muestra, frecuentemente las primeras 1.000 filas. **No usar su tamaño para certificar el total.** En el perfilado de columnas, elegir conjunto de datos completo cuando se utilice para validación.

Crear temporalmente una **Referencia** de cada consulta base y desactivar **Habilitar carga** para las consultas auxiliares. En cada auxiliar, Transformar → Contar filas. Alternativamente, la barra de fórmulas puede contener estas expresiones de **Power Query M**, no medidas DAX:

```powerquery
Table.RowCount(#"vw_tickets")
```

```powerquery
Table.RowCount(#"vw_ticket_events")
```

```powerquery
Table.RowCount(#"vw_ticket_state_durations")
```

Cada auxiliar debe depender de la consulta base al final de sus pasos aplicados y evaluar el conjunto completo. No sustituir las tres consultas principales por sus conteos. No cargar los auxiliares como tablas del modelo. Registrar resultados, fecha de actualización y cualquier error. Después de Cerrar y aplicar, contrastar también el número de filas cargadas indicado por Desktop y comprobar que las tres tablas figuren en el modelo.

### B. Claves, duplicados y huérfanos

En otras **referencias auxiliares sin carga**, para tickets/eventos conservar sólo ticket_id/event_id, comprobar ausencia de NULL, quitar duplicados **sólo en la referencia de validación** y contar filas; el resultado debe coincidir con su conteo original. Para estados, seleccionar conjuntamente ticket_id y estado antes de quitar duplicados y contar. No deduplicar las consultas base para forzar una validación.

Para huérfanos: combinar una referencia de cada hija con una referencia de la lista de ticket_id de tickets, mediante **anti izquierda**, usando ticket_id de tipo entero en ambos lados. Deben devolver **0 filas**. La prueba no modifica el modelo ni filtra los datos de origen.

### C. Referencia SQL opcional de sólo lectura

Si cambian los datos o hay diferencias, ejecutar manualmente en SSMS, base HelpDeskAnalytics, para obtener el total actual del origen:

```sql
SELECT N'vw_tickets' AS vista, COUNT_BIG(*) AS filas
FROM bi.vw_tickets
UNION ALL
SELECT N'vw_ticket_events', COUNT_BIG(*) FROM bi.vw_ticket_events
UNION ALL
SELECT N'vw_ticket_state_durations', COUNT_BIG(*)
FROM bi.vw_ticket_state_durations;
```

Comparar contra Power Query **después de una actualización completa**, sin filtros. Si SQL cambió desde Fase 3.6, actualizar la evidencia; no afirmar que los totales históricos siguen vigentes por definición. Si SQL no cambió, revisar Navegación, filtros, errores, habilitación de carga y caché. En esta fase documental no se ejecutó esa consulta de nuevo.

## 5. Calidad y conservación: controles manuales adicionales

Estas verificaciones se pueden realizar con filtros y conteos en referencias auxiliares sin carga, sin DAX y sin filtrar las consultas principales. Valores de referencia de Fase 3.6:

| Control | Referencia esperada |
|---|---:|
| Tickets prioridad unknown | 33.965 |
| Tickets resolución NULL | 853 |
| Eventos valor NULL | 1.840 |
| Tickets sin historial observado | 41, con cantidad_eventos=0 |
| Tickets elegible_done=True | 62.034 |
| Tickets elegible_otra_resolucion=True | 3.804 |
| Tickets dq_has_problem=True | 450; no excluirlos automáticamente |
| Tickets distintos con alguna duración negativa | 55; no confundir filas de estados con tickets distintos |
| Estados distintos | 20; no incluir wf_total_time como estado |
| Filas con duracion_cero=True | 2; ambas distintas de duración NULL |

Comprobar que duracion_segundos_exacta y __raw siguen siendo texto, que los negativos siguen siendo negativos y que las fechas desde 2007 permanecen. Estado final closed/done no implica éxito, y unknown no equivale a Low. Las columnas de elegibilidad y calidad siguen disponibles para filtros posteriores; no agregar todavía medidas de mediana, P90 o SLA.

## 6. Columnas que podrían ocultarse, conservándolas

Usar **Ocultar en la vista de informe** desde el modelo, según la versión de Desktop. No usar Quitar columnas en Power Query ni eliminar campos en SQL. Ocultar no es una medida de seguridad: los datos siguen en el modelo, ocupan espacio y pueden volver a mostrarse.

| Grupo | Columnas candidatas | Motivo / precaución |
|---|---|---|
| Claves técnicas | ticket_id de las tres tablas, event_id | Las relaciones siguen funcionando; conservar para auditoría y futuras medidas |
| Procedencia | dq_source_row de tickets y eventos | Es entero de fila CSV, no flag ni medida de calidad |
| Texto original de eventos | id__raw, issueid__raw, change_group_id__raw, created__raw | Auditoría; nunca convertir sus tipos |
| Agrupación técnica de eventos | grupo_cambio_id | No es identificador de ticket ni número de cambios |
| Precisión exacta | duracion_segundos_exacta | Copia textual útil para auditar el DECIMAL de SQL |
| Intervalos de auditoría | intervalo_calendario_segundos, wf_total_time_segundos | Evitar confundirlos con el tiempo calendario elegible |
| Metadato global | inicio_historial_observado_utc | Es inicio de cobertura de la extracción, no métrica dinámica |
| Diagnóstico técnico | dq_invalid_*, dq_missing_*, dq_naive_*, dq_duplicate_* y flags detallados | Mantener accesibles para diagnóstico; documentar si se ocultan |

Mantener inicialmente visibles los atributos de filtros, elegibilidad, dq_has_problem y los indicadores negativos/NULL/cero/no recorrido. No ocultar todos los flags por comodidad: dq_missing_optional puede describir ausencias legítimas, y dq_duration_comparable=True no significa que los tiempos coincidan. Los __raw completos de tickets no están en vw_tickets; su auditoría original sigue en stg, consultable por la clave si se requiere, sin cargar otra tabla en este modelo.

## 7. Advertencias de precisión, UTC y doble conteo

- **Decimal:** SQL conserva DECIMAL(38,16), pero Número decimal en Power BI es aproximado, con hasta 15 dígitos significativos. Número decimal fijo utiliza cuatro posiciones decimales y tampoco preserva las 16 del origen. Formatear a dos decimales sólo cambia presentación. No usar igualdad entre floats como prueba de calidad; conservar los flags SQL y el texto exacto de auditoría.
- **Fechas:** las vistas normalizaron a UTC antes de retirar el offset. DATETIME2 no lleva zona incorporada: mantener la convención _utc. No aplicar desplazamiento de Lima ni convertir a hora local. El modelo puede reducir precisión temporal; no recalcular duraciones a partir de las fechas importadas para exigir equivalencia a 100 ns. Usar las duraciones numéricas ya calculadas cuando se definan medidas.
- **Granularidad:** una fila de estados no es un ticket ni una visita. Unir las dos tablas hijas multiplica eventos por estados. Los 1.333.820 registros no representan 1.333.820 tickets. No sumar el calendario de tickets repetido en una tabla plana ni sumar el volumen de eventos de tickets y el de eventos como si fueran poblaciones diferentes.
- **Propagación:** filtros de tickets alcanzan ambas hijas. Filtros exclusivos de evento/estado no vuelven a tickets con dirección única. Los conteos preagregados por ticket no responden a un filtro de fecha/campo aplicado sólo a eventos; eso se resolverá con indicadores futuros sobre el grano correcto, sin habilitar bidireccionalidad.
- **Cobertura:** tickets desde 2007, eventos desde 2015 y corte observado en marzo de 2023. No filtrar antigüedad por defecto. Cohortes recientes pueden estar censuradas y meses incompletos requieren señalización. Los tiempos son calendario, no horas efectivas; no hay objetivos contractuales para calcular SLA.

Referencias: [tipos de datos](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-data-types) y [propagación de relaciones](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand).

## 8. Lista de comprobación manual pendiente

Las casillas vacías son intencionales: documentar pasos no prueba haberlos completado en Desktop.

- [ ] Confirmar la instancia y HelpDeskAnalytics mediante autenticación segura en Desktop.
- [ ] Confirmar modo Importar y sólo tres consultas base bi, sin copias de stg.
- [ ] Revisar todos los tipos por columna y establecer No resumir donde corresponda.
- [ ] Confirmar UTC sin desplazamientos y conservación de NULL, unknown y negativos.
- [ ] Contar el conjunto completo: 66.691 / 257.508 / 1.333.820, o documentar un cambio real del origen.
- [ ] Verificar claves sin NULL, unicidad de tickets/eventos y unicidad compuesta de estados.
- [ ] Verificar 0 huérfanos en referencias anti izquierda.
- [ ] Crear/verificar exactamente dos relaciones activas 1:*, de tickets hacia las hijas, filtro único.
- [ ] Revisar y evitar relaciones automáticas adicionales, muchos-a-muchos o bidireccionales.
- [ ] Contrastar los controles de calidad de la sección 5 sin alterar las consultas base.
- [ ] Ocultar sólo campos técnicos acordados en la vista de informe; conservarlos en el modelo/origen.
- [ ] Desactivar carga de consultas auxiliares y confirmar las tres tablas cargadas tras Cerrar y aplicar.
- [ ] Registrar manualmente fecha, versión de Desktop, resultados y discrepancias antes de avanzar.
- [ ] Guardar el PBIX local en powerbi/HelpDesk_Analytics.pbix, sin versionar datos ni publicar credenciales.

La siguiente fase podrá definir medidas DAX y visualizaciones una vez validado el modelo. Esta guía no incluye fórmulas DAX, no genera datos ficticios y no acredita configuración interna del PBIX existente.
