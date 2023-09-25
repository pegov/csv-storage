# csv-storage

- Получение списка файлов с названием колонок
- Получение данных из конкретного файла в json формате с опциональными фильтрацией и сортировкой по одному или нескольким столбцам
- Удаление файлов
- Dockerfile для запуска сервиса в Docker
- Хранение файлов в папке "resources"

## API
- `GET /api/csv` - Получить информацию о всех файлах и колонках
- `POST /api/csv` - Загрузить новый файл
	- `curl -X POST -F file=@test.csv http://127.0.0.1:8000/api/csv`
	- `curl -X POST -F file=@test.csv -F overwrite=1 http://127.0.0.1:8000/api/csv` - Перезаписать при конфликте
- `GET /api/csv/{filename}` - Получение данных из конкретного файла в json формате с опциональными фильтрацией и сортировкой по одному или нескольким столбцам
	- `GET /api/csv/ign?sort_by=score_desc` - Отсортировать записи по колонке "score" в убывающем порядке
	- `GET /api/csv/ign?sort_by=score_asc` - Отсортировать записи по колонке "score" в возрастающем порядке
	- `GET /api/csv/ign?sort_by=score_desc&sort_by=release_year_asc` - Отсортировать записи по колонке "score" в убывающем порядке и по колонке "release_year" в возрастающем порядке 
	- `GET /api/csv/tornados?filter_key=yr&filter_value=2010` - Найти записи, в которых колонка "yr" равна 2010
	- `GET /api/csv/tornados?filter_key=yr&filter_value=1951&filter_key=mo&filter_value=12&sort_by=dy_desc` - Найти записи, в которых колонка "yr" равна 1951, колонка "mo" равна 12 и отсортировать по колонке "dy" в убывающем порядке
- `DELETE /api/csv/{filename}` - Удаление файла
	- `curl -X DELETE http://127.0.0.1:8000/api/csv/test`

## Deploy
```sh
docker build -f Dockerfile.prod -t csv-storage-prod .
docker run -it -p 8000:8000 -v ./:/app csv-storage-prod
# или
./scripts/prod
```

## Development
```sh
docker build -f Dockerfile.dev -t csv-storage-dev .
docker run -it -p 8000:8000 -v ./:/app csv-storage-dev
# или
./scripts/dev

# или напрямую через poetry
poetry install
poetry run python uvicorn app.main:app --reload --port 8000
```

## Formatting, linting and testing
```sh
./scripts/format
./scripts/check
./scripts/test
```
