# Comprobación del entorno SQL Server — 2026-11-13

**Actualización Fase 3.3:** conexión SQL funcional; creación e importación confirmadas el 2026-11-14 UTC (2026-11-13 en Lima). ODBC 18.07.0001, SQL Server 17.0.1000.7, 66.691 tickets y 257.508 eventos. Ver [sql_load_report.md](sql_load_report.md). El diagnóstico siguiente se conserva como antecedente de los errores ya superados.

- Registro ODBC y `pyodbc.drivers()` confirman **ODBC Driver 17 for SQL Server** y **ODBC Driver 18 for SQL Server**, además del controlador antiguo `SQL Server`.
- `Get-OdbcDriver` falló por acceso denegado a CIM; se usaron el registro y pyodbc como comprobaciones alternativas.
- Servicio `MSSQLSERVER`: Running; `MSSQLFDLauncher`: Running; `SQLBrowser`: Stopped. Esto identifica una instancia local predeterminada, no acredita conectividad ni permisos.
- `sqlcmd` no fue encontrado en PATH.
- pyodbc no estaba instalado en `.venv`; se instaló **5.5.0**. Pandas **2.3.3**, Python **3.13.2**. python-dotenv ya estaba disponible.
- Intentos de autenticación integrada a `master`, con timeout de 5 segundos: localhost y memoria compartida `lpc:localhost`, driver 18; también driver 17 con memoria compartida. Todos fallaron con **SQLSTATE 08001**.
- Diagnóstico devuelto por el controlador: «No se admite el cifrado en el cliente» y «No hay credenciales disponibles en el paquete de seguridad» (SSL, código -2146893042), seguido de un mensaje genérico de instancia/red. También falló el intento fuera del sandbox. No permite concluir que SQL Server esté caído.
- Para aislar el error se probaron localmente TrustServerCertificate=yes y Encrypt=no; no resolvieron la conexión. La configuración entregada conserva **Encrypt=yes, TrustServerCertificate=no**.
- No se obtuvo versión del servidor, no se pudo comprobar si HelpDeskAnalytics existe y no se verificaron permisos de creación. No hubo conexión exitosa ni ejecución de DDL o importación.

## Qué falta

Ejecutar el diagnóstico desde una sesión Windows con credenciales válidas y acceso al servicio. Verificar primero acceso con SSMS, protocolo/instancia y configuración TLS/certificado; si persiste, reparar la configuración del cliente ODBC/seguridad. No se han cambiado servicios, protocolos ni certificados. Si se usa autenticación SQL, habilitarla y configurar las credenciales sólo en el entorno local.

Una vez conecte a master, ejecutar manualmente los scripts 01 y 02 en orden. La carga queda para la siguiente fase: conversión explícita por columna, tickets antes del histórico, transacción y reconciliación de conteos, nulos, flags y claves. No utilizar una carga que descarte silenciosamente errores o convierta nulos/negativos para forzar restricciones.

## Validaciones realizadas

- Perfil completo: issues 66.691 × 102 (8 __raw, 36 dq_*); histórico 257.508 × 28 (4 __raw, 18 dq_*).
- Tipos, nulabilidad obligatoria, rango BIGINT, DECIMAL(38,16) exacto, longitudes UTF-16, fechas UTC y precisión de 100 ns: superados en todos los valores no vacíos.
- PK únicas/no nulas y relación referencial: superadas.
- SQLFluff 3.5.0, dialecto tsql: scripts 01 y 02 aceptados. El CLI requiere `--ignore-local-config` en este entorno porque no puede enumerar el directorio del usuario; también se verificó el parser por API sin configuración externa.
- Suite original: 6 pruebas de limpieza superadas. Suite nueva: 6 pruebas de esquema/conexión superadas, incluido parser T-SQL. Se comprobaron cobertura exacta de columnas y ausencia de instrucciones de carga/borrado en el DDL.
- Generación comparó SHA-256 antes/después de cada CSV procesado: intactos. Los dos hashes de raw coinciden con `reports/data_quality.md`.
- Limitación: parser y pruebas locales no sustituyen compilación en SQL Server, comprobación de permisos ni validación del catálogo existente. Esas comprobaciones siguen pendientes.
