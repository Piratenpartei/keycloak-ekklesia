import logging
import sys

import typer
from eliot import to_file
from eliot.stdlib import EliotHandler

from departments import department_parser, department_updater

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(EliotHandler())
to_file(sys.stdout)
logging.captureWarnings(True)

app = typer.Typer()


@app.command()
def parse(json_path: str, csv_path: str):
    department_parser.parse(json_path, csv_path)


@app.command()
def update(json_path: str):
    department_updater.update(json_path)


if __name__ == "__main__":
    app()
