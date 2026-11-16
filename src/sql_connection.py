"""Configuración ODBC por entorno y diagnóstico exclusivamente SELECT."""
import os
from pathlib import Path


def connection_string(env=None):
    env = os.environ if env is None else env
    def escaped(value):
        return "{" + value.replace("}", "}}") + "}"
    server = env.get("SQL_SERVER", "").strip()
    if not server:
        raise ValueError("Define SQL_SERVER explícitamente")
    auth = env.get("SQL_AUTH", "windows").lower()
    if auth not in {"windows", "sql"}:
        raise ValueError("SQL_AUTH debe ser windows o sql")
    options = {"DRIVER": env.get("SQL_DRIVER", "ODBC Driver 18 for SQL Server"),
               "SERVER": server, "DATABASE": env.get("SQL_DATABASE", "HelpDeskAnalytics")}
    for key, default in (("SQL_ENCRYPT", "yes"), ("SQL_TRUST_SERVER_CERTIFICATE", "no")):
        if env.get(key, default).lower() not in {"yes", "no"}:
            raise ValueError(f"{key} debe ser yes o no")
    options["Encrypt"] = env.get("SQL_ENCRYPT", "yes")
    options["TrustServerCertificate"] = env.get("SQL_TRUST_SERVER_CERTIFICATE", "no")
    if auth == "windows":
        options["Trusted_Connection"] = "yes"
    else:
        if not env.get("SQL_USER") or not env.get("SQL_PASSWORD"):
            raise ValueError("Autenticación SQL requiere SQL_USER y SQL_PASSWORD")
        options.update(UID=env["SQL_USER"], PWD=env["SQL_PASSWORD"])
    return ";".join(f"{key}={escaped(value)}" for key, value in options.items())


def connect(database=None, *, autocommit=True):
    """Carga .env sin pisar el entorno; permite elegir base y transacción."""
    import pyodbc
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    settings = dict(os.environ)
    if database is not None:
        settings["SQL_DATABASE"] = database
    return pyodbc.connect(connection_string(settings), timeout=5, autocommit=autocommit)


def main():
    import pyodbc
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    print("Controladores ODBC:", pyodbc.drivers())
    try:
        connection = connect()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128)), DB_NAME(), DB_ID(N'HelpDeskAnalytics')")
            version, database, target_id = cursor.fetchone()
            print(f"Conexión OK; versión={version}; base={database}; HelpDeskAnalytics existe={target_id is not None}")
        finally:
            connection.close()
    except ValueError as error:
        print(f"Configuración incompleta: {error}")
        return 1
    except pyodbc.Error as error:
        # No imprimir conexión, usuario, contraseña ni mensajes que los repitan.
        print(f"Conexión fallida; SQLSTATE={error.args[0] if error.args else 'desconocido'}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
