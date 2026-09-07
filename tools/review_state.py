"""Private, locked checkpoints for explicitly resumed external review attempts."""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
import uuid
from typing import Iterator


class StateError(RuntimeError):
    pass


class ReviewState:
    def __init__(self, path: Path, data: dict):
        self.path = path
        self.data = data

    @classmethod
    @contextlib.contextmanager
    def open(cls, directory: Path, identity: dict, resume: Path | None = None) -> Iterator["ReviewState"]:
        """Hold one process lock from checkpoint loading through final posting."""
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent = directory.lstat()
        if stat.S_ISLNK(parent.st_mode) or not stat.S_ISDIR(parent.st_mode):
            raise StateError("review state directory must be a real directory")
        if parent.st_uid != os.getuid() or parent.st_mode & 0o077:
            raise StateError("review state directory must be owned by this user with mode 0700")
        directory = directory.resolve()
        path = resume.absolute() if resume is not None else directory / f"{uuid.uuid4().hex}.json"
        # A resume path names a file directly in the configured private directory.
        if path.parent.resolve() != directory or path.parent.is_symlink():
            raise StateError("resume file must be directly inside the review state directory")
        path = directory / path.name
        lock_path = directory / (path.name + ".lock")
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "a") as lock:
                lock_stat = os.fstat(lock.fileno())
                if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_uid != os.getuid() or lock_stat.st_mode & 0o077:
                    raise StateError("review state lock must be a private regular file owned by this user")
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise StateError("this review attempt is already running; wait for it to finish") from error
                if resume is not None:
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    with os.fdopen(fd) as source:
                        info = os.fstat(source.fileno())
                        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                            raise StateError("resume file must be a private regular file owned by this user")
                        data = json.load(source)
                    if not isinstance(data, dict) or data.get("version") != 1 or data.get("identity") != identity:
                        raise StateError("resume identity differs: repository, PR head/base, prompt, providers, or bridge code changed; start a fresh review")
                    if not isinstance(data.get("providers"), dict) or not isinstance(data.get("history"), list):
                        raise StateError("malformed review checkpoint; start a fresh review")
                else:
                    data = {"version": 1, "identity": identity, "providers": {}, "history": [], "created_at": datetime.now(timezone.utc).isoformat()}
                state = cls(path, data)
                state.save()
                yield state
        except (OSError, ValueError) as error:
            raise StateError(f"could not read or write private review state: {type(error).__name__}") from error

    def save(self) -> None:
        fd, name = tempfile.mkstemp(prefix=".review-", dir=self.path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "w") as output:
                json.dump(self.data, output, indent=2)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
            directory_fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)

    def record(self, provider: str, status: str, **values: object) -> None:
        entry = {"status": status, **values}
        self.data["providers"][provider] = entry
        self.data["history"].append({"provider": provider, "status": status, "at": datetime.now(timezone.utc).isoformat(), **({"diagnostic": values["diagnostic"]} if "diagnostic" in values else {})})
        self.save()
