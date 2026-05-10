import os
import uuid

import pandas as pd
from langchain_core.tools import tool

from app.config import settings


def create_csv_export_tool(db_engine):
    """Create a CSV export tool that uses the given database engine."""

    @tool
    def export_to_csv(sql_query: str, file_name: str) -> str:
        """Export the results of a SQL query to a CSV file.

        Use this tool when the user asks to convert, export, or download data as CSV.

        Args:
            sql_query: A valid SQL SELECT query to execute.
            file_name: A descriptive name for the output file (without extension).

        Returns:
            The file path of the created CSV file.
        """
        os.makedirs(settings.EXPORT_DIR, exist_ok=True)
        df = pd.read_sql(sql_query, db_engine)
        safe_name = file_name.replace(" ", "_").replace("/", "_")
        out_path = os.path.join(
            settings.EXPORT_DIR, f"{uuid.uuid4().hex}_{safe_name}.csv"
        )
        df.to_csv(out_path, index=False)
        return f"CSV file created at: {out_path}"

    return export_to_csv
