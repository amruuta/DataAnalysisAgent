import pandas as pd
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime


def convert_csv_to_sqlite(
    csv_file_path: str, output_dir: str = None, db_name: str = None
) -> str:
    """
    Convert a CSV file to a SQLite database.

    Args:
        csv_file_path: Path to the CSV file to convert
        output_dir: Directory where the SQLite database will be saved (defaults to same as CSV)
        db_name: Name of the SQLite database file (defaults to CSV filename with .db extension)

    Returns:
        str: The SQLite database URL

    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        Exception: If conversion fails
    """

    # Validate CSV file exists
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

    if not csv_path.suffix.lower() == ".csv":
        raise ValueError(f"File must be a CSV file, got: {csv_path.suffix}")

    # Set default output directory (same as CSV file location)
    if output_dir is None:
        output_dir = csv_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Set default database name (CSV filename with .db extension)
    if db_name is None:
        db_name = csv_path.stem + ".db"

    db_path = output_dir / db_name
    table_name = csv_path.stem  # Use CSV filename as table name

    try:
        print(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_file_path)
        print(
            f"✓ CSV loaded successfully with {len(df)} rows and {len(df.columns)} columns"
        )

        # Create SQLite connection
        db_url = f"sqlite:///{db_path.as_posix()}"
        sqlite_url = f"sqlite:///{db_path.as_posix()}"

        # Also create a standard sqlite:/// URL
        conn_string = (
            f"sqlite:///{str(db_path).replace(chr(92), '/')}"  # Replace backslashes
        )

        print(f"Creating SQLite database: {db_path}")
        conn = sqlite3.connect(str(db_path))

        # Write dataframe to SQLite
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()

        print(f"✓ Database created successfully")
        print(f"✓ Table name: {table_name}")

        return str(db_path)

    except Exception as e:
        raise Exception(f"Error converting CSV to SQLite: {str(e)}")


def save_db_url_to_file(db_path: str, output_file: str = None) -> str:
    """
    Save the SQLite database URL to a text file.

    Args:
        db_path: Full path to the SQLite database file
        output_file: Path to the output text file (defaults to db_info.txt in same directory)

    Returns:
        str: Path to the output file
    """

    db_path_obj = Path(db_path)

    if output_file is None:
        output_file = db_path_obj.parent / "db_info.txt"
    else:
        output_file = Path(output_file)

    # Create database URL in different formats
    db_absolute_path = db_path_obj.resolve()  # Get absolute path
    db_url_absolute = f"sqlite:///{db_absolute_path.as_posix()}"
    db_url_sqlite = f"sqlite:///{db_path_obj.as_posix()}"
    db_url_standard = f"sqlite:///{str(db_path).replace(chr(92), '/')}"
    db_url_relative = f"sqlite:///{db_path_obj.name}"

    # Get file info
    file_size = os.path.getsize(db_path) / 1024  # Size in KB
    creation_time = datetime.fromtimestamp(os.path.getctime(db_path))

    # Write to file
    with open(output_file, "w") as f:
        f.write("SQLite Database Information\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Database File: {db_path}\n")
        f.write(f"Absolute Path: {db_absolute_path}\n")
        f.write(f"File Size: {file_size:.2f} KB\n")
        f.write(f"Created: {creation_time}\n\n")
        f.write("Database URLs:\n")
        f.write("-" * 50 + "\n")
        f.write(f"Absolute Path URL:\n{db_url_absolute}\n\n")
        f.write(f"Standard SQLite URL:\n{db_url_standard}\n\n")
        f.write(f"POSIX Path URL:\n{db_url_sqlite}\n\n")
        f.write(f"Relative URL:\n{db_url_relative}\n\n")
        f.write("-" * 50 + "\n")
        f.write(f"Connection String (for SQLAlchemy):\n")
        f.write(f"{db_url_absolute}\n")

    return str(output_file)


def main():
    """Main function to process CSV files."""

    # Check command line arguments
    if len(sys.argv) < 2:
        print(
            "Usage: python csv_sqlite_converter.py <csv_file_path> [output_dir] [db_name] [info_file]"
        )
        print("\nExample:")
        print("  python csv_sqlite_converter.py data.csv")
        print(
            "  python csv_sqlite_converter.py data.csv ./database my_database.db db_info.txt"
        )
        sys.exit(1)

    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    db_name = sys.argv[3] if len(sys.argv) > 3 else None
    info_file = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        # Convert CSV to SQLite
        db_path = convert_csv_to_sqlite(csv_file, output_dir, db_name)

        # Save database URL to text file
        info_file_path = save_db_url_to_file(db_path, info_file)

        print(f"\n✓ Database URL saved to: {info_file_path}\n")

        # Display the database URL
        with open(info_file_path, "r") as f:
            print(f.read())

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
