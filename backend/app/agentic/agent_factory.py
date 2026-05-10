from typing import cast

from deepagents import create_deep_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.redis import RedisSaver
from sqlalchemy import create_engine

from app.agentic.tools.csv_export import create_csv_export_tool
from app.agentic.tools.plotly_chart import create_plotly_chart_tool
from app.agentic.tools.pptx_export import create_pptx_export_tool
from app.config import settings
from app.models import DataSource

SYSTEM_PROMPT = """\
You are a data analysis assistant. You have access to SQL database tools to \
query and analyze data.

When the user asks you to analyze data, use the SQL tools to explore the \
database schema and run queries.

When the user asks to export, convert, or download data as a CSV file, use \
the export_to_csv tool. First write a SELECT query for the data the user \
wants, then pass it to export_to_csv.

When the user asks for visualizations, graphs, charts, or plotting, use the \
create_plotly_chart tool with a SQL SELECT query and appropriate columns.

When the user asks for a PowerPoint, slide deck, presentation, or PPTX file, \
delegate the work to the pptx_generator subagent. The final answer must include \
the PPTX link returned by that subagent.

Always explain your findings clearly.
"""

PPTX_SUBAGENT_PROMPT = """\
You are a PPTX generation specialist for data analysis conversations.

Your job is a two-step process:
1. Plan the presentation as JSON.
2. Call create_pptx_from_plan with that JSON to generate the .pptx file.

Use SQL tools to inspect the relevant schema and build SELECT queries for the \
content needed in the deck. Keep the deck focused and useful: 4-7 slides is \
usually enough.

The JSON plan must be an object with:
- title: presentation title
- subtitle: short context line
- file_name: short file name without extension
- slides: list of slide objects

Each slide object may include:
- title: slide title
- bullets: 2-5 short bullets
- takeaway: optional main point
- chart: optional object with sql_query, chart_type (bar, line, pie), x_column, \
y_column, title, max_rows
- table: optional object with sql_query and max_rows

Use only SELECT queries. After create_pptx_from_plan returns a link, respond with \
the generated file link and a one-sentence summary of what the deck covers.
"""

_checkpointer = None


def _get_checkpointer() -> RedisSaver:
    """Create or reuse the Redis checkpointer used for agent memory."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = RedisSaver(redis_url=settings.REDIS_URL)
        _checkpointer.setup()
    return _checkpointer


def create_agent_for_datasource(data_source: DataSource):
    """Build a deep agent wired to the correct database for a data source."""
    llm = ChatLiteLLM(
        model=settings.AI_MODEL,
        api_key=settings.AI_API_KEY,
    )

    source_type = cast(str, data_source.source_type)
    table_name = cast(str, data_source.table_name)

    if source_type == "file":
        sql_db = SQLDatabase.from_uri(
            settings.DATABASE_URL,
            include_tables=[table_name],
        )
        db_engine = create_engine(settings.DATABASE_URL)
    else:
        db_url = cast(str, data_source.db_url)
        sql_db = SQLDatabase.from_uri(
            db_url,
            include_tables=([table_name] if table_name != "all_tables" else None),
        )
        db_engine = create_engine(db_url)

    toolkit = SQLDatabaseToolkit(db=sql_db, llm=llm)
    sql_tools = toolkit.get_tools()

    csv_tool = create_csv_export_tool(db_engine)
    plotly_tool = create_plotly_chart_tool(db_engine)
    pptx_tool = create_pptx_export_tool(db_engine)
    all_tools = sql_tools + [csv_tool, plotly_tool, pptx_tool]

    return create_deep_agent(
        model=llm,
        tools=all_tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=[
            {
                "name": "pptx_generator",
                "description": (
                    "Plan and generate PowerPoint/PPTX slide decks from the "
                    "selected data source. Use proactively for presentation requests."
                ),
                "system_prompt": PPTX_SUBAGENT_PROMPT,
                "tools": [*sql_tools, pptx_tool],
            }
        ],
        checkpointer=_get_checkpointer(),
    )
