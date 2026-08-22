"""
Supervises the FastAPI backend, restarting the uvicorn worker if it exits or
stops answering health checks. Deliberately does NOT pass --reload to uvicorn:
on Windows, --reload forces the worker onto asyncio's SelectorEventLoop (see
uvicorn/loops/asyncio.py), which has a hard ~512 file-descriptor ceiling and
crashes under load (real incident, 2026-08-19). This watchdog is a plain
polling loop with no ASGI app and no event loop of its own, so it never hits
that ceiling, and it recovers from worker crashes or hangs the way --reload
would have -- without reload's Windows failure mode.
"""

import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PORT = 8001
HEALTH_URL = f"http://127.0.0.1:{PORT}/health"
CHECK_INTERVAL_S = 5
HEALTH_TIMEOUT_S = 6  # this machine runs at ~1GB free RAM under normal load;
# a healthy request can legitimately take 2-3s, so a tight timeout produces
# false-positive restarts rather than catching real hangs
FAILURE_THRESHOLD = 4  # consecutive failed health checks before restart
STARTUP_GRACE_S = 8  # don't health-check until the worker has had time to boot
RESTART_BACKOFF_S = 2

UVICORN_CMD = [
    sys.executable,
    "-m",
    "uvicorn",
    "app.main:app",
    "--port",
    str(PORT),
    "--app-dir",
    str(BACKEND_DIR),
]

_child: subprocess.Popen | None = None


def _log(msg: str) -> None:
    print(f"[watchdog] {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def _kill_stale_port_owner(port: int) -> None:
    # If a previous watchdog instance was hard-killed (e.g. by the dev tooling's
    # own stop, which may not reach past the trampoline hop either), its worker
    # can be left orphaned holding the port. Clear it before binding again.
    if sys.platform != "win32":
        return
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-NetTCPConnection -LocalPort {port} -State Listen "
                "-ErrorAction SilentlyContinue).OwningProcess",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return
    pid = result.stdout.strip().splitlines()[0].strip() if result.stdout.strip() else ""
    if pid.isdigit():
        _log(f"port {port} already held by stale process {pid}, killing its tree")
        subprocess.run(["taskkill", "/F", "/T", "/PID", pid], capture_output=True)
        time.sleep(1)


def _start_worker() -> subprocess.Popen:
    _log(f"starting worker: {' '.join(UVICORN_CMD)}")
    return subprocess.Popen(UVICORN_CMD, cwd=BACKEND_DIR)


def _stop_worker(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        # This machine's venv python.exe launchers are trampolines that re-exec
        # into a child process rather than being the interpreter directly, so
        # proc.pid is only the immediate hop -- the real uvicorn process is a
        # grandchild. proc.terminate() alone would leave it orphaned holding
        # the port. taskkill /T kills the whole process tree.
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _log("worker did not exit in time, killing")
        proc.kill()
        proc.wait(timeout=5)


def _health_ok() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=HEALTH_TIMEOUT_S) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def _cleanup_and_exit(signum, frame) -> None:
    _log(f"received signal {signum}, shutting down worker")
    if _child is not None:
        _stop_worker(_child)
    sys.exit(0)


def main() -> None:
    global _child
    signal.signal(signal.SIGINT, _cleanup_and_exit)
    signal.signal(signal.SIGTERM, _cleanup_and_exit)

    _kill_stale_port_owner(PORT)
    _child = _start_worker()
    consecutive_failures = 0
    last_start = time.monotonic()

    while True:
        time.sleep(CHECK_INTERVAL_S)

        exit_code = _child.poll()
        if exit_code is not None:
            _log(f"worker exited unexpectedly (code {exit_code}), restarting")
            time.sleep(RESTART_BACKOFF_S)
            _child = _start_worker()
            last_start = time.monotonic()
            consecutive_failures = 0
            continue

        if time.monotonic() - last_start < STARTUP_GRACE_S:
            continue

        if _health_ok():
            consecutive_failures = 0
            continue

        consecutive_failures += 1
        _log(f"health check failed ({consecutive_failures}/{FAILURE_THRESHOLD})")
        if consecutive_failures >= FAILURE_THRESHOLD:
            _log("worker unresponsive, restarting")
            _stop_worker(_child)
            time.sleep(RESTART_BACKOFF_S)
            _child = _start_worker()
            last_start = time.monotonic()
            consecutive_failures = 0


if __name__ == "__main__":
    main()
