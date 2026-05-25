from qmtclient import QmtClient

client = QmtClient("http://127.0.0.1:8000", token=None)
for event in client.events():
    print(event)
