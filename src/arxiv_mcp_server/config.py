import os
from pathlib import Path

from appdirs import user_data_dir, user_log_dir

APP_NAME = "arxiv-mcp-server"
DATABASE_PATH = Path(
    os.environ.get(
        "ARXIV_MCP_DB_PATH",
        str(Path(user_data_dir(APP_NAME)) / "papers.db"),
    )
)
LOG_PATH = Path(
    os.environ.get(
        "ARXIV_MCP_LOG_PATH",
        str(Path(user_log_dir(APP_NAME)) / f"{APP_NAME}.log"),
    )
)
