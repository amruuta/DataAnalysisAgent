import base64
import json
import uuid
from typing import Any, cast

import numpy as np
import pandas as pd
import plotly.express as px
import structlog
from langchain_core.tools import tool
from plotly.utils import PlotlyJSONEncoder

from app.tools.plotly_registry import register_chart

_SUPPORTED_CHART_TYPES = {"bar", "line", "scatter", "pie", "histogram"}
logger = structlog.get_logger(__name__)

_DTYPE_MAP: dict[str, np.dtype] = {
    "f8": np.dtype("float64"),
    "f4": np.dtype("float32"),
    "i8": np.dtype("int64"),
    "i4": np.dtype("int32"),
    "i2": np.dtype("int16"),
    "i1": np.dtype("int8"),
    "u8": np.dtype("uint64"),
    "u4": np.dtype("uint32"),
    "u2": np.dtype("uint16"),
    "u1": np.dtype("uint8"),
    "b1": np.dtype("bool"),
}


def _decode_plotly_typed_array(value: dict) -> list | dict:
    dtype_code = value.get("dtype")
    encoded_data = value.get("bdata")
    shape = value.get("shape")

    if not isinstance(dtype_code, str) or not isinstance(encoded_data, str):
        return value

    dtype = _DTYPE_MAP.get(dtype_code)
    if dtype is None:
        return value

    try:
        raw = base64.b64decode(encoded_data)
        array = np.frombuffer(raw, dtype=dtype)
        if isinstance(shape, list) and shape:
            array = array.reshape(tuple(shape))
        return array.tolist()
    except Exception:
        return value


def _normalize_plotly_payload(value):
    if isinstance(value, dict):
        if "dtype" in value and "bdata" in value:
            decoded = _decode_plotly_typed_array(value)
            if not isinstance(decoded, dict):
                return decoded
        return {key: _normalize_plotly_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_plotly_payload(item) for item in value]
    return value


def _serialize_figure(figure) -> dict:
    """Convert Plotly figure into JSON-safe dict (no numpy arrays)."""
    serialized = json.loads(json.dumps(figure.to_plotly_json(), cls=PlotlyJSONEncoder))
    return cast(dict[str, Any], _normalize_plotly_payload(serialized))


def _build_figure(
    df: pd.DataFrame,
    chart_type: str,
    x_column: str,
    y_column: str | None,
    color_column: str | None,
    title: str,
):
    if x_column not in df.columns:
        raise ValueError(f"Column '{x_column}' is not present in query results.")

    if color_column and color_column not in df.columns:
        raise ValueError(
            f"Color column '{color_column}' is not present in query results."
        )

    if chart_type in {"bar", "line", "scatter", "pie"}:
        if not y_column:
            raise ValueError(f"'{chart_type}' chart requires a y_column.")
        if y_column not in df.columns:
            raise ValueError(f"Column '{y_column}' is not present in query results.")

    if chart_type == "bar":
        fig = px.bar(df, x=x_column, y=y_column, color=color_column, title=title)
    elif chart_type == "line":
        fig = px.line(df, x=x_column, y=y_column, color=color_column, title=title)
    elif chart_type == "scatter":
        fig = px.scatter(df, x=x_column, y=y_column, color=color_column, title=title)
    elif chart_type == "pie":
        fig = px.pie(
            df, names=x_column, values=y_column, color=color_column, title=title
        )
    else:
        fig = px.histogram(df, x=x_column, color=color_column, title=title)

    fig.update_layout(template="plotly_white")
    return fig


def create_plotly_chart_tool(db_engine):
    """Create a Plotly chart-generation tool backed by pandas DataFrames."""

    @tool
    def create_plotly_chart(
        sql_query: str,
        chart_type: str,
        x_column: str,
        y_column: str | None = None,
        title: str | None = None,
        color_column: str | None = None,
        max_rows: int = 1000,
    ) -> str:
        """Generate a Plotly chart from SQL query results.

        Use this tool when the user asks for chart, graph, plot, or visualization.

        Args:
            sql_query: A SQL SELECT query that returns chart data.
            chart_type: Chart type: bar, line, scatter, pie, or histogram.
            x_column: Column name for x-axis (or pie labels).
            y_column: Column name for y-axis (required for bar, line, scatter, pie).
            title: Optional chart title.
            color_column: Optional column to split/segment by color.
            max_rows: Max rows to read from SQL query (1-5000).

        Returns:
            A status message with the generated chart ID.
        """
        normalized_type = chart_type.strip().lower()
        logger.info(
            "plotly_chart_requested",
            chart_type=normalized_type,
            x_column=x_column,
            y_column=y_column,
            color_column=color_column,
            max_rows=max_rows,
        )

        if normalized_type not in _SUPPORTED_CHART_TYPES:
            logger.error("plotly_chart_unsupported_type", chart_type=normalized_type)
            return "Unsupported chart_type. Use one of: " + ", ".join(
                sorted(_SUPPORTED_CHART_TYPES)
            )

        sql = sql_query.strip().rstrip(";")
        if not sql.lower().startswith("select"):
            logger.error("plotly_chart_non_select_query")
            return "Only SELECT queries are allowed for create_plotly_chart."

        bounded_max_rows = min(max(max_rows, 1), 5000)
        wrapped_query = f"SELECT * FROM ({sql}) AS chart_data LIMIT {bounded_max_rows}"

        try:
            df = pd.read_sql(wrapped_query, db_engine)
        except Exception as exc:
            logger.error("plotly_chart_query_failed", error=str(exc))
            return f"Failed to execute query for chart generation: {exc}"

        if df.empty:
            logger.info("plotly_chart_empty_result")
            return "Query returned no rows. No chart was generated."

        chart_title = title or f"{normalized_type.title()} chart"

        try:
            figure = _build_figure(
                df=df,
                chart_type=normalized_type,
                x_column=x_column,
                y_column=y_column,
                color_column=color_column,
                title=chart_title,
            )
        except ValueError as exc:
            logger.error("plotly_chart_build_failed", error=str(exc))
            return f"Chart generation failed: {exc}"

        chart_id = uuid.uuid4().hex
        register_chart(
            {
                "chart_id": chart_id,
                "title": chart_title,
                "chart_type": normalized_type,
                "figure": _serialize_figure(figure),
            }
        )

        logger.info(
            "plotly_chart_created",
            chart_id=chart_id,
            chart_type=normalized_type,
            row_count=int(len(df)),
        )

        return (
            f"Chart created successfully with chart_id={chart_id}. "
            "It will be returned to the frontend in the chat response."
        )

    return create_plotly_chart
