from pathlib import Path
import click


@click.group()
def main() -> None:
    pass


default_listens_file = (
    Path.home() / ".local" / "share" / "offline_listens" / "listens.json"
)


@main.command(short_help="add a listen")
@click.option("-n", "--now", is_flag=True, help="if true, sets the listen time to now")
@click.argument(
    "LISTENS_FILE",
    required=True,
    type=click.Path(path_type=Path),
    default=default_listens_file,
    envvar="OFFLINE_LISTENS_FILE",
)
def listen(now: bool, listens_file: Path) -> None:
    """
    Add a listen to your listens file

    If the OFFLINE_LISTENS_FILE environment variable is set,
    it will be used as the listens file. Otherwise, this stores in
    ~/.local/share/offline_listens/listens.json
    """
    from .listens import prompt, Listen

    from autotui.shortcuts import load_from, dump_to

    if not listens_file.parent.exists():
        listens_file.parent.mkdir(parents=True, exist_ok=True)

    picked = prompt(now)
    items = load_from(Listen, listens_file, allow_empty=True)
    items.append(picked)
    dump_to(items, listens_file)


@main.command(short_help="update cache file")
def update_cache() -> None:
    """
    Updates the offline listens cache file.
    """
    from .listens import update_cache

    click.echo("Updating offline listens cache...")
    update_cache()
    click.echo("Done.")


@main.command(short_help="parse an offline listens file")
@click.argument(
    "LISTENS_FILE",
    required=True,
    type=click.Path(path_type=Path),
    default=default_listens_file,
    envvar="OFFLINE_LISTENS_FILE",
)
def parse(listens_file: Path) -> None:
    """
    Parses an offline listens file, and prints the output to stdout.
    """
    import datetime

    import simplejson

    from .parse import parse_file

    data = list(parse_file(listens_file))

    def _default(o: object) -> str:
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        raise TypeError

    click.echo(simplejson.dumps(data, namedtuple_as_object=True, default=_default))


@main.command(short_help="dump listens")
def dump() -> None:
    """
    Dumps the output of the listens command, to confirm that the command
    is working as expected.
    """
    import json

    from .listens import fetch_listens

    for listen in fetch_listens():
        click.echo(
            json.dumps(
                {
                    "artist": listen.artist,
                    "album": listen.album,
                    "track": listen.track,
                }
            )
        )


if __name__ == "__main__":
    main(prog_name="offline_listens")
