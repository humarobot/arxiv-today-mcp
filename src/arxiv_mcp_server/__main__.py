from arxiv_mcp_server.server import mcp


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
