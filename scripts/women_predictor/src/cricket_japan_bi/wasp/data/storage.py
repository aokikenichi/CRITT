"""Buffered Parquet writers and the isolated WASP DuckDB materialization."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

from .schemas import TABLE_SCHEMAS, arrow_schema, conform_row
from .audit import sha256_file


PathLike = Union[str, Path]
TABLE_NAMES = tuple(TABLE_SCHEMAS)
BASE_TABLE_NAMES = tuple(
    name for name in TABLE_NAMES if name != "model_ready_states"
)


class BufferedParquetWriter:
    """Write dictionaries in bounded batches with an explicit stable schema."""

    def __init__(
        self,
        table_name: str,
        output_path: PathLike,
        buffer_size: int = 50_000,
        compression: str = "zstd",
    ) -> None:
        if table_name not in TABLE_SCHEMAS:
            raise KeyError("unknown normalized table: {}".format(table_name))
        if buffer_size <= 0:
            raise ValueError("buffer_size must be positive")
        try:
            import pyarrow.parquet as pq
        except ImportError as exc:  # pragma: no cover - installation dependent
            raise RuntimeError("PyArrow is required to write normalized data") from exc

        self.table_name = table_name
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.temp_path = self.output_path.with_name(self.output_path.name + ".tmp")
        self.schema = arrow_schema(table_name)
        self._pq = pq
        self._writer = pq.ParquetWriter(
            str(self.temp_path), self.schema, compression=compression
        )
        self._buffer: List[Mapping[str, Any]] = []
        self.row_count = 0
        self.buffer_size = buffer_size
        self._closed = False

    def append(self, row: Mapping[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("cannot append to a closed Parquet writer")
        self._buffer.append(conform_row(self.table_name, row))
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def extend(self, rows: Iterable[Mapping[str, Any]]) -> None:
        for row in rows:
            self.append(row)

    def flush(self) -> None:
        if not self._buffer:
            return
        import pyarrow as pa

        table = pa.Table.from_pylist(self._buffer, schema=self.schema)
        self._writer.write_table(table)
        self.row_count += len(self._buffer)
        self._buffer = []

    def close(self) -> int:
        if self._closed:
            return self.row_count
        try:
            self.flush()
            self._writer.close()
            # ParquetWriter already emits a valid schema-only file when there
            # are no rows, so every normalized table is always present.
            os.replace(str(self.temp_path), str(self.output_path))
            self._closed = True
            return self.row_count
        except Exception:
            try:
                self._writer.close()
            finally:
                if self.temp_path.exists():
                    self.temp_path.unlink()
            raise

    def abort(self) -> None:
        if self._closed:
            return
        try:
            self._writer.close()
        finally:
            if self.temp_path.exists():
                self.temp_path.unlink()
            self._closed = True

    def __enter__(self) -> "BufferedParquetWriter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is None:
            self.close()
        else:
            self.abort()


class NormalizedDatasetWriters:
    """Own one buffered writer for each normalized table."""

    def __init__(self, output_dir: PathLike, buffer_size: int = 50_000) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.writers = {
            name: BufferedParquetWriter(
                name, self.output_dir / "{}.parquet".format(name), buffer_size
            )
            for name in BASE_TABLE_NAMES
        }

    def append(self, table_name: str, row: Mapping[str, Any]) -> None:
        self.writers[table_name].append(row)

    def close(self) -> Mapping[str, int]:
        counts: Dict[str, int] = {}
        try:
            for name in BASE_TABLE_NAMES:
                counts[name] = self.writers[name].close()
        except Exception:
            for writer in self.writers.values():
                writer.abort()
            raise
        return counts

    def abort(self) -> None:
        for writer in self.writers.values():
            writer.abort()

    def __enter__(self) -> "NormalizedDatasetWriters":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is None:
            self.close()
        else:
            self.abort()


def _sql_string(value: str) -> str:
    return "'{}'".format(value.replace("'", "''"))


def write_duckdb(
    output_dir: PathLike,
    database_path: Optional[PathLike] = None,
    parquet_paths: Optional[Mapping[str, PathLike]] = None,
) -> Path:
    """Materialize only the WASP tables into a dedicated DuckDB database."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - installation dependent
        raise RuntimeError("DuckDB is required to materialize wasp.duckdb") from exc

    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = Path(database_path).resolve() if database_path else root / "wasp.duckdb"
    temp = target.with_name(target.name + ".tmp")
    if temp.exists():
        temp.unlink()
    paths = {
        name: Path(parquet_paths[name]).resolve()
        if parquet_paths and name in parquet_paths
        else root / "{}.parquet".format(name)
        for name in TABLE_NAMES
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "normalized Parquet file(s) missing: {}".format(", ".join(missing))
        )

    connection = duckdb.connect(str(temp))
    try:
        for name in TABLE_NAMES:
            connection.execute(
                'CREATE TABLE "{}" AS SELECT * FROM read_parquet({})'.format(
                    name, _sql_string(str(paths[name]))
                )
            )
        connection.execute(
            "CREATE INDEX matches_match_id_idx ON matches(match_id)"
        )
        connection.execute(
            "CREATE INDEX states_match_innings_idx ON states(match_id, innings, state_sequence)"
        )
        connection.execute(
            "CREATE INDEX deliveries_match_innings_idx ON deliveries(match_id, innings, source_sequence)"
        )
        connection.execute(
            "CREATE INDEX prematch_match_team_idx ON prematch_team_features(match_id, team)"
        )
        connection.execute(
            "CREATE INDEX model_ready_match_innings_idx ON model_ready_states(match_id, innings, state_sequence)"
        )
        connection.execute(
            "CREATE TABLE dataset_metadata(schema_version VARCHAR, created_at TIMESTAMP DEFAULT current_timestamp)"
        )
        from .schemas import SCHEMA_VERSION

        connection.execute(
            "INSERT INTO dataset_metadata(schema_version) VALUES (?)", [SCHEMA_VERSION]
        )
        connection.close()
        os.replace(str(temp), str(target))
    except Exception:
        connection.close()
        if temp.exists():
            temp.unlink()
        raise
    return target


def write_json_atomic(path: PathLike, payload: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(str(temporary), str(target))
    return target


def read_manifest(path: PathLike) -> Mapping[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("dataset manifest must be a JSON object")
    return payload


def validate_processed_dataset(
    output_dir: PathLike,
    *,
    expected_config_hash: Optional[str] = None,
    verify_hashes: bool = True,
) -> Mapping[str, Any]:
    """Validate the published processed generation before a consumer reads it."""

    root = Path(output_dir).expanduser().resolve()
    incomplete = root / ".build-in-progress.json"
    if incomplete.exists():
        raise RuntimeError(
            "processed WASP generation is incomplete; rerun scripts.prepare_data"
        )
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("processed WASP manifest is missing: {}".format(manifest_path))
    manifest = read_manifest(manifest_path)
    if expected_config_hash and manifest.get("config_hash") != expected_config_hash:
        raise RuntimeError(
            "processed config SHA mismatch: expected {}, found {}".format(
                expected_config_hash, manifest.get("config_hash")
            )
        )
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        raise RuntimeError("processed manifest has no file integrity contract")
    row_counts = manifest.get("row_counts") or {}
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - required production dependency
        raise RuntimeError("PyArrow is required to validate processed data") from exc
    for name in TABLE_NAMES:
        metadata = files.get(name)
        if not isinstance(metadata, Mapping):
            raise RuntimeError("processed manifest missing file entry: {}".format(name))
        path = root / str(metadata.get("path") or "{}.parquet".format(name))
        if not path.is_file():
            raise FileNotFoundError("processed file is missing: {}".format(path))
        if verify_hashes and sha256_file(path) != metadata.get("sha256"):
            raise RuntimeError("processed SHA-256 mismatch for {}".format(name))
        actual_rows = int(pq.ParquetFile(path).metadata.num_rows)
        expected_rows = int(metadata.get("rows", row_counts.get(name, -1)))
        if actual_rows != expected_rows or actual_rows != int(row_counts.get(name, -1)):
            raise RuntimeError(
                "processed row-count mismatch for {}: manifest={} parquet={}".format(
                    name, expected_rows, actual_rows
                )
            )
        descriptor = json.dumps(
            list(TABLE_SCHEMAS[name].items()), separators=(",", ":")
        ).encode("utf-8")
        expected_schema = hashlib.sha256(descriptor).hexdigest()
        if metadata.get("schema_sha256") != expected_schema:
            raise RuntimeError("processed schema contract mismatch for {}".format(name))
    if verify_hashes and isinstance(files.get("duckdb"), Mapping):
        database = root / str(files["duckdb"].get("path") or "wasp.duckdb")
        if not database.is_file() or sha256_file(database) != files["duckdb"].get("sha256"):
            raise RuntimeError("processed SHA-256 mismatch for wasp.duckdb")
    return manifest


__all__ = [
    "BufferedParquetWriter",
    "BASE_TABLE_NAMES",
    "NormalizedDatasetWriters",
    "TABLE_NAMES",
    "read_manifest",
    "validate_processed_dataset",
    "write_duckdb",
    "write_json_atomic",
]
