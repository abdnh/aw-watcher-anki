import os
import sys
from concurrent.futures import Future
from datetime import datetime, timezone
from time import sleep

import requests
from anki.collection import Collection
from aqt import gui_hooks, mw
from aqt.utils import showWarning

ADDON_NAME = "ActivityWatch for Anki"
ADDON_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(ADDON_DIR, "vendor"))

# pylint: disable=wrong-import-position
from aw_client import ActivityWatchClient
from aw_client.config import load_config
from aw_core.models import Event

CONFIG = mw.addonManager.getConfig(__name__)
PULSE_TIME = 60


def watch() -> None:
    client = ActivityWatchClient("anki-client", testing=CONFIG["testing"])
    bucket_id = f"anki-watcher_{client.client_hostname}"
    client.create_bucket(bucket_id, event_type="app.anki.review")
    poll_time = float(CONFIG["poll_time"])

    with client:
        while mw.col:
            card = mw.reviewer.card
            if card:
                cid = card.id
                nid = card.nid
                deck = mw.col.decks.name(card.did)
                heartbeat_data = {"cid": cid, "deck": deck, "nid": nid}
                now = datetime.now(timezone.utc)
                heartbeat_event = Event(timestamp=now, data=heartbeat_data)
                client.heartbeat(
                    bucket_id,
                    heartbeat_event,
                    pulsetime=PULSE_TIME,
                    queued=True,
                    commit_interval=4.0,
                )
            sleep(poll_time)


def on_done(fut: Future) -> None:
    try:
        fut.result()
    except requests.exceptions.ConnectionError:
        aw_config = load_config()
        server_config = aw_config[
            "server" if not CONFIG["testing"] else "server-testing"
        ]
        server_port = server_config["port"]
        showWarning(
            f"""Failed to connect to ActivityWatch. Make sure it's running on port {server_port} \
then restart Anki.""",
            mw,
            title=ADDON_NAME,
        )


def on_collection_did_load(col: Collection) -> None:
    mw.taskman.run_in_background(watch, on_done)


gui_hooks.collection_did_load.append(on_collection_did_load)
