from qmtclient import EventReplay, FakeQmtClient, load_jsonl


def main() -> None:
    client = FakeQmtClient.from_fixture("examples/fixtures/offline_strategy.json")

    print("tick:", client.market.get_full_tick(["000001.SZ"]))
    print("asset:", client.account.asset("example-account"))
    print("orders:", client.account.cached_orders())

    events = load_jsonl("examples/fixtures/events.jsonl")
    for event in EventReplay(events, types=["stock_trade"]):
        print("event:", event)


if __name__ == "__main__":
    main()
