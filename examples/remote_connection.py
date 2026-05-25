import os

from qmtclient import QmtClient


def main() -> None:
    base_url = os.environ.get("QMTCLIENT_BASE_URL", "http://192.168.1.10:8000")
    token = os.environ.get("QMTCLIENT_TOKEN")
    api_version = os.environ.get("QMTCLIENT_API_VERSION", "v1")
    client = QmtClient(
        base_url,
        token=token,
        api_version=None if api_version.lower() == "none" else api_version,
    )

    print("base_url:", client.base_url)
    print("health:", client.health())
    print("status:", client.status())
    print("methods:", client.methods())


if __name__ == "__main__":
    main()
