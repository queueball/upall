#!/usr/bin/env python3
import concurrent.futures
import dataclasses
import functools
import pathlib
import subprocess
import typing

VIM_BUNDLE = pathlib.Path("~/.vim/bundle/").expanduser()


@dataclasses.dataclass
class Command:
    handler: typing.Callable[[object], None]
    params: object


def to_stdout_cache(route, content):
    path = "~/.stdout/"
    target = pathlib.Path(path + route).expanduser()
    target.parent.mkdir(exist_ok=True)
    with open(target, "w") as f:
        f.write(content.decode())


def validate(func):
    @functools.wraps(func)
    def inner(cwd):
        if not (cwd / ".git").exists():
            return
        if cwd.stem in {
            "YouCompleteMe",  # This requires running install, so we'll skip updating it
        }:
            return
        return func(cwd)

    return inner


@validate
def _run_git_pull(cwd: pathlib.Path):
    result = subprocess.check_output(["git", "pull"], cwd=cwd, stderr=subprocess.STDOUT)
    to_stdout_cache(cwd.name + ".txt", result)


def _run_cmd_list(cmd: list):
    result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    to_stdout_cache("_".join(cmd) + ".txt", result)


if __name__ == "__main__":
    cmds = [Command(_run_git_pull, cwd) for cwd in sorted(VIM_BUNDLE.iterdir())] + [
        Command(_run_cmd_list, ["brew", "upgrade"]),
        Command(_run_cmd_list, ["brew", "cleanup"]),
        Command(_run_cmd_list, ["brew", "doctor"]),
        Command(subprocess.call, "pydeps"),
    ]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(cmd.handler, cmd.params) for cmd in cmds]

    subprocess.call("check_outputs_py")
    subprocess.call("parse_brew_upgrade")
