import sys
from pathlib import Path

import pytest
from harlequin.duck_ops import (
    _get_columns,
    _get_databases,
    _get_schemas,
    _get_tables,
    connect,
    get_catalog,
)
from harlequin.exception import HarlequinExit


def test_connect(tiny_db: Path, small_db: Path, tmp_path: Path) -> None:
    assert connect([])
    assert connect([":memory:"])
    assert connect([tiny_db], read_only=False)
    assert connect([tiny_db], read_only=True)
    assert connect([tiny_db, Path(":memory:"), small_db], read_only=False)
    assert connect([tiny_db, small_db], read_only=True)
    assert connect([tmp_path / "new.db"])
    assert connect([], allow_unsigned_extensions=True)
    assert connect([tiny_db], allow_unsigned_extensions=True)
    assert connect([tiny_db, small_db], read_only=True)


@pytest.mark.online
def test_connect_extensions() -> None:
    assert connect([], extensions=None)
    assert connect([], extensions=[])
    assert connect([], extensions=["spatial"])
    assert connect([], allow_unsigned_extensions=True, extensions=["spatial"])


@pytest.mark.xfail(
    sys.platform == "win32",
    reason="PRQL extension not yet built for Windows and DuckDB v0.8.1.",
)
@pytest.mark.online
def test_connect_prql() -> None:
    # Note: this may fail in the future if the extension doesn't support the latest
    # duckdb version.
    assert connect(
        [],
        allow_unsigned_extensions=True,
        extensions=["prql"],
        custom_extension_repo="welsch.lu/duckdb/prql/latest",
        force_install_extensions=True,
    )


@pytest.mark.skipif(
    sys.version_info[0:2] != (3, 10), reason="Matrix is hitting MD too many times."
)
@pytest.mark.online
def test_connect_motherduck(tiny_db: Path) -> None:
    # note: set environment variable motherduck_token
    assert connect(["md:"])
    assert connect(["md:cloudf1"], md_saas=True)
    assert connect(["md:", tiny_db])


def test_cannot_connect(tiny_db: Path) -> None:
    with pytest.raises(HarlequinExit):
        connect([Path(":memory:")], read_only=True)
    with pytest.raises(HarlequinExit):
        connect([tiny_db, Path(":memory:")], read_only=True)


def test_get_databases(tiny_db: Path, small_db: Path) -> None:
    conn = connect([tiny_db, small_db])
    assert _get_databases(conn) == [("small",), ("tiny",)]


def test_get_schemas(small_db: Path) -> None:
    conn = connect([small_db], read_only=True)
    assert _get_schemas(conn, "small") == [("empty",), ("main",)]


def test_get_tables(small_db: Path) -> None:
    conn = connect([small_db], read_only=True)
    assert _get_tables(conn, "small", "empty") == []
    assert _get_tables(conn, "small", "main") == [("drivers", "BASE TABLE")]


def test_get_columns(small_db: Path) -> None:
    conn = connect([small_db], read_only=True)
    assert _get_columns(conn, "small", "main", "drivers") == [
        ("code", "VARCHAR"),
        ("dob", "DATE"),
        ("driverId", "BIGINT"),
        ("driverRef", "VARCHAR"),
        ("forename", "VARCHAR"),
        ("nationality", "VARCHAR"),
        ("number", "VARCHAR"),
        ("surname", "VARCHAR"),
        ("url", "VARCHAR"),
    ]


def test_get_catalog(tiny_db: Path, small_db: Path) -> None:
    conn = connect([tiny_db, small_db], read_only=True)
    expected = [
        (
            "small",
            [
                ("empty", []),
                (
                    "main",
                    [
                        (
                            "drivers",
                            "BASE TABLE",
                            [
                                ("code", "VARCHAR"),
                                ("dob", "DATE"),
                                ("driverId", "BIGINT"),
                                ("driverRef", "VARCHAR"),
                                ("forename", "VARCHAR"),
                                ("nationality", "VARCHAR"),
                                ("number", "VARCHAR"),
                                ("surname", "VARCHAR"),
                                ("url", "VARCHAR"),
                            ],
                        )
                    ],
                ),
            ],
        ),
        ("tiny", [("main", [("foo", "BASE TABLE", [("foo_col", "INTEGER")])])]),
    ]
    assert get_catalog(conn) == expected
