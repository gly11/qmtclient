import os

from qmtclient import QmtClient


def main() -> None:
    client = QmtClient(
        os.environ.get("QMTCLIENT_BASE_URL", "http://192.168.1.10:8000"),
        token=os.environ.get("QMTCLIENT_TOKEN"),
    )
    account_id = os.environ.get("QMTCLIENT_ACCOUNT_ID", "example-account")

    print("tick:", client.market.get_full_tick(["000001.SZ"]))
    print("asset:", client.account.asset(account_id))
    print("positions:", client.account.positions(account_id))
    print("cached orders:", client.account.cached_orders(limit=20))

    # Real trading permission, dry-run behavior, limits, and audit are enforced by qmtserver.
    # Uncomment only against a server intentionally configured for trading tests.
    # print(client.trading.order_stock(account_id, "000001.SZ", 23, 100, 5, 10.5))


if __name__ == "__main__":
    main()
