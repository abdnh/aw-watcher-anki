import os
import sys
from concurrent.futures import Future
from datetime import datetime, timezone
from time import sleep

import requests
from anki.collection import Collection
from anki.utils import pointVersion
from aqt import gui_hooks, mw
from aqt.utils import showWarning

sys.path.append(os.path.join(os.path.dirname(__file__), "vendor"))

from aw_client import ActivityWatchClient
from aw_client.config import load_config
from aw_core.models import Event

from .config import config
from .consts import consts
from .log import logger

PULSE_TIME = 60


def watch() -> None:
    logger.info("Starting watcher...")
    client = ActivityWatchClient("anki-client", testing=config["testing"])
    bucket_id = f"anki-watcher_{client.client_hostname}"
    client.create_bucket(bucket_id, event_type="app.anki.review")
    poll_time = float(config["poll_time"])

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
            "server" if not config["testing"] else "server-testing"
        ]
        server_port = server_config["port"]
        showWarning(
            f"""Failed to connect to ActivityWatch. Make sure it's running on port {server_port} \
then restart Anki.""",
            mw,
            title=consts.name,
        )


def on_collection_did_load(col: Collection) -> None:
    if pointVersion() >= 230100:
        # pylint: disable=unexpected-keyword-arg
        mw.taskman.run_in_background(watch, on_done, uses_collection=False)  # type: ignore
    else:
        mw.taskman.run_in_background(watch, on_done)


gui_hooks.collection_did_load.append(on_collection_did_load)
