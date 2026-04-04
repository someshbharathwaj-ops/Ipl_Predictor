"""Pipeline entrypoint for producing IPL training datasets."""

from __future__ import annotations

from preprocessing import load_raw_tables


def main() -> None:
    """Load the repository datasets."""

    tables = load_raw_tables()
    print({name: frame.shape for name, frame in tables.items()})


if __name__ == "__main__":
    main()
