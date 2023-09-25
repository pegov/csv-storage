import os
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, Form, HTTPException, Query, UploadFile

ROOT = Path("resources")


class CSVFile:
    filename: str
    df: pd.DataFrame

    def __init__(self, filename: str, df: pd.DataFrame):
        self.filename = filename
        self.df = df

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "columns": self.df.columns.to_list(),
        }


def load_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.fillna(0)
    return df


def load_all_files(path: Path) -> list[CSVFile]:
    files: list[CSVFile] = []
    for file in os.listdir(path):
        if file.endswith(".csv"):
            df = load_file(path / file)
            files.append(CSVFile(file, df))

    return files


app = FastAPI()


@app.get("/api/csv")
async def csv_get_files():
    files = load_all_files(ROOT)
    return [file.to_dict() for file in files]


@app.get("/api/csv/{filename}")
async def csv_get_file(
    filename: str,
    filter_key: Annotated[list[str] | None, Query()] = None,
    filter_value: Annotated[list[str] | None, Query()] = None,
    sort_by: Annotated[list[str] | None, Query()] = None,
):
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"

    path = Path(ROOT) / filename
    if not path.exists():
        raise HTTPException(404)

    df = load_file(path)

    if filter_key is not None and filter_value is not None:
        if len(filter_key) != len(filter_value):
            raise HTTPException(400, detail="filter length mismatch")

        for k, v in zip(filter_key, filter_value):
            if k not in df.columns:
                raise HTTPException(
                    400, detail=f'field "{v}" does not exist in file {filename}'
                )

            if pd.api.types.is_string_dtype(df[k]):
                df = df[df[k] == v]
            elif pd.api.types.is_integer_dtype(df[k]):
                df = df[df[k] == int(v)]
            elif pd.api.types.is_float_dtype(df[k]):
                df = df[df[k] == float(v)]
            else:
                pass

    if sort_by is not None:
        fields: list[str] = []
        ascending: list[bool] = []
        for s in sort_by:
            values = s.rsplit("_", 1)
            if len(values) == 2:
                field, order = values
            else:
                field = s
                order = "desc"  # default

            order = order.lower()
            if order != "asc" and order != "desc":
                raise HTTPException(
                    400,
                    detail=f'wrong order value "{order}"',
                )

            if field not in df.columns:  # type: ignore
                raise HTTPException(
                    400, detail=f'field "{field}" does not exist in file {filename}'
                )

            fields.append(field)
            ascending.append(order == "asc")

        df = df.sort_values(by=fields, ascending=ascending)

    return df.to_dict("records")


@app.post("/api/csv")
async def csv_upload_file(
    file: UploadFile,
    overwrite: Annotated[str | None, Form()] = None,
):
    should_overwrite = overwrite is not None and (
        overwrite == "1" or overwrite.lower() == "true"
    )

    if file.filename is None:
        raise HTTPException(400, detail="missing filename")

    if not file.filename.endswith(".csv"):
        raise HTTPException(400, detail="wrong file format")

    path = Path(ROOT) / file.filename

    if path.exists() and not should_overwrite:
        raise HTTPException(409)  # file already exists

    with open(path, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename}


@app.delete("/api/csv/{filename}")
async def csv_delete_file(filename: str):
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"

    path = Path(ROOT) / filename
    if not path.exists():
        raise HTTPException(404)

    os.remove(path)

    return None
