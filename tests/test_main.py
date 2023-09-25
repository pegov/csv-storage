import os
import shutil

from fastapi.testclient import TestClient

from app.main import ROOT, app

client = TestClient(app)

NAME = "tornados.csv"


def test_csv_get_files():
    response = client.get("/api/csv")
    assert response.status_code == 200

    filenames = [item["filename"] for item in response.json()]
    for file in os.listdir(ROOT):
        if file.endswith(".csv"):
            assert file in filenames


def test_csv_get_file_filter():
    params = {"filter_key": "yr", "filter_value": "1950"}
    response = client.get(f"/api/csv/{NAME}", params=params)
    assert response.status_code == 200
    data = response.json()
    for row in data:
        assert str(row.get("yr")) == "1950"


def test_csv_get_file_filter_multiple():
    params = {
        "filter_key": ["yr", "mo"],
        "filter_value": ["1950", "12"],
    }
    response = client.get(f"/api/csv/{NAME}", params=params)
    assert response.status_code == 200
    data = response.json()
    for row in data:
        assert str(row.get("yr")) == "1950" and str(row.get("mo")) == "12"


def test_csv_get_file_sort_default():
    params = {
        "filter_key": "yr",
        "filter_value": "1950",
        "sort_by": "dy",
    }
    response = client.get(f"/api/csv/{NAME}", params=params)
    assert response.status_code == 200
    data = response.json()
    assert all(data[i]["dy"] >= data[i + 1]["dy"] for i in range(len(data) - 1))


def test_csv_get_file_sort_desc():
    params = {
        "filter_key": "yr",
        "filter_value": "1950",
        "sort_by": "dy_desc",
    }
    response = client.get(f"/api/csv/{NAME}", params=params)
    assert response.status_code == 200
    data = response.json()
    assert all(data[i]["dy"] >= data[i + 1]["dy"] for i in range(len(data) - 1))


def test_csv_get_file_sort_asc():
    params = {
        "filter_key": "yr",
        "filter_value": "1950",
        "sort_by": "dy_asc",
    }
    response = client.get(f"/api/csv/{NAME}", params=params)
    assert response.status_code == 200
    data = response.json()
    assert all(data[i]["dy"] <= data[i + 1]["dy"] for i in range(len(data) - 1))


def test_csv_get_file_not_found():
    response = client.get("/api/csv/not_found")
    assert response.status_code == 404


def test_csv_upload_file_wrong_file_format():
    with open("./app/main.py", "rb") as f:
        data = f.read()
        files = {"file": ("main.py", data)}
        response = client.post("/api/csv", files=files)
        assert response.status_code == 400


def test_csv_upload_file_mssing_filename():
    with open(ROOT / NAME, "rb") as f:
        data = f.read()
        files = {"file": data}
        response = client.post("/api/csv", files=files)
        assert response.status_code == 400


def test_csv_upload_file_conflict():
    with open(ROOT / NAME, "rb") as f:
        data = f.read()
        files = {"file": (NAME, data)}
        response = client.post("/api/csv", files=files)
        assert response.status_code == 409


def test_csv_upload_file_overwrite():
    with open(ROOT / NAME, "rb") as f:
        b = f.read()
        files = {"file": (NAME, b)}
        data = {"overwrite": "1"}
        response = client.post("/api/csv", files=files, data=data)
        assert response.status_code == 200
        assert response.json() == {"filename": NAME}


def test_csv_delete_file():
    name_to_delete = "test.csv"
    shutil.copyfile(ROOT / NAME, ROOT / name_to_delete)
    response = client.delete(f"/api/csv/{name_to_delete}")
    assert response.status_code == 200


def test_csv_delete_file_not_found():
    name_to_delete = "test.csv"
    response = client.delete(f"/api/csv/{name_to_delete}")
    assert response.status_code == 404
