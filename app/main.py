import os
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, UploadFile, Form

ROOT = Path("resources")


class CSVFile:
    filename: str
    reader: pd.DataFrame

    def __init__(self, filename: str, data: pd.DataFrame):
        self.filename = filename
        self.data = data

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "columns": self.data.columns.to_list(),
        }


def load_file(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    data = data.fillna(0)
    return data


def load_all_files(path: Path) -> list[CSVFile]:
    files: list[CSVFile] = []
    for file in os.listdir(path):
        if file.endswith(".csv"):
            data = load_file(path / file)
            files.append(CSVFile(file, data))

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

    data = load_file(path)

    res: list[dict]
    if filter_key is not None and filter_value is not None:
        if len(filter_key) != len(filter_value):
            raise HTTPException(400, detail="filter length mismatch")

        res = []
        for _, row in data.iterrows():
            found = True
            for k, v in zip(filter_key, filter_value):
                if k not in data.columns:  # type: ignore
                    raise HTTPException(
                        400, detail=f'field "{v}" does not exist in file {filename}'
                    )
                if str(row[k]) != v:
                    found = False
                    break

            if found:
                res.append(row.to_dict())

    else:
        res = [row.to_dict() for _, row in data.iterrows()]

    if sort_by is not None:
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

            if field not in data.columns:  # type: ignore
                raise HTTPException(
                    400, detail=f'field "{field}" does not exist in file {filename}'
                )

            res.sort(key=lambda x: x[field], reverse=order == "desc")

    return res


@app.post("/api/csv")
async def csv_upload_file(
    file: UploadFile,
    overwrite: Annotated[str | None, Form()] = None,
):
    should_overwrite = overwrite is not None and (
        overwrite == "1" or overwrite.lower() == "true"
    )
    assert type(file.filename) is str
    if not file.filename.endswith("csv"):
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
