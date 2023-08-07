import os
import sys
import json
from datetime import datetime

from typing import List, NamedTuple, Iterator, Generator, Dict, Any, Optional


class Source(NamedTuple):
    artist: str
    album: str
    track: str


class Listen(NamedTuple):
    artist: str
    track: str
    album: Optional[str]
    when: datetime


def fetch_commands() -> List[str]:
    """
    Feteches the commands from the OFFLINE_LISTENS_COMMANDS environment variable.
    """

    items = os.environ.get("OFFLINE_LISTENS_COMMANDS", "")
    cmds = [cmd for cmd in items.split(":") if cmd.strip()]
    if not cmds:
        print(
            "Warning: no commands found in OFFLINE_LISTENS_COMMANDS environment variable",
            file=sys.stderr,
        )
    return cmds


def yield_listens(command: str) -> Generator[Source, None, None]:
    """
    Yields listens from a command.
    """
    import shlex
    import subprocess

    if not command:
        return

    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    assert process.stdout is not None
    for line in process.stdout:
        try:
            listen = json.loads(line)
        except json.JSONDecodeError:
            continue
        yield Source(
            artist=listen["artist"],
            album=listen["album"],
            # fetch from track or title
            track=listen.get("track", listen.get("title", "")),
        )


def fetch_listens() -> Iterator[Source]:
    for command in fetch_commands():
        if not command:
            print("Passed an empty command", file=sys.stderr)
            continue
        for listen in yield_listens(command):
            yield listen


CACHE_FILE = os.path.expanduser("~/.cache/offline-listens.json")


def read_cache() -> List[Source]:
    if not os.path.exists(CACHE_FILE):
        return update_cache()
    else:
        with open(CACHE_FILE) as f:
            return [
                Source(
                    artist=listen["artist"],
                    album=listen["album"],
                    track=listen["track"],
                )
                for listen in json.load(f)
            ]


def update_cache() -> List[Source]:
    """
    Updates the cache file.
    """
    listens = list(fetch_listens())
    with open(CACHE_FILE, "w") as f:
        json.dump([listen._asdict() for listen in listens], f)
    return listens


def prompt(now: bool) -> Listen:
    import click
    from autotui.pick import pick_namedtuple
    from autotui.namedtuple_prompt import prompt_namedtuple

    picked = pick_namedtuple(read_cache())
    if picked is None:
        click.echo("No listens picked", err=True)
        return prompt_namedtuple(Listen)
    else:
        data: Dict[str, Any] = {
            "artist": picked.artist,
            "album": picked.album,
            "track": picked.track,
        }
        if now:
            data["when"] = datetime.now()
        return prompt_namedtuple(Listen, attr_use_values=data)
