"""Inspección inicial de archivos CSV de tickets de soporte."""

import argparse
from pathlib import Path
import sys

import pandas as pd


def inspect_csv(path: Path, separator: str, encoding: str) -> None:
    """Carga un CSV e imprime su estructura y controles básicos de calidad."""
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró un archivo CSV en: {path}. "
            "Si todavía no tienes el dataset, descárgalo manualmente desde "
            "la fuente indicada en README.md y colócalo en data/raw/."
        )

    data = pd.read_csv(path, sep=separator, encoding=encoding, low_memory=False)
    nulls = data.isna().sum()
    summary = pd.DataFrame(
        {
            "columna": data.columns,
            "tipo": data.dtypes.astype(str).to_numpy(),
            "nulos": nulls.to_numpy(),
            "nulos (%)": (nulls / len(data) * 100).round(2).to_numpy()
            if len(data)
            else 0.0,
        }
    )

    print(f"Archivo: {path.resolve()}")
    print(f"Filas: {len(data):,}")
    print(f"Columnas: {len(data.columns):,}")
    print(f"Valores nulos totales: {int(nulls.sum()):,}")
    print(f"Filas duplicadas completas (sin contar la primera): {int(data.duplicated().sum()):,}")
    print("\nColumnas, tipos inferidos y valores nulos:")
    print(summary.to_string(index=False))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Examina columnas, tipos, filas, nulos y duplicados de un CSV."
    )
    parser.add_argument("csv_path", type=Path, help="Ruta al archivo CSV")
    parser.add_argument("--sep", default=",", help="Separador del CSV (predeterminado: coma)")
    parser.add_argument("--encoding", default="utf-8", help="Codificación (predeterminada: utf-8)")
    args = parser.parse_args()

    if len(args.sep) != 1:
        parser.error("El separador debe tener exactamente un carácter.")

    try:
        inspect_csv(args.csv_path, args.sep, args.encoding)
    except (OSError, UnicodeError, LookupError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
