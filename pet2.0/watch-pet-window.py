"""Apply the pet workaround once after launch, then exit without polling."""
import argparse
import ctypes as c
import datetime
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from ctypes import wintypes as w

ROOT = Path(__file__).resolve().parent
MUTEX = "Local\\CodexPetClickFixWatcher"
STOP = "Local\\CodexPetClickFixStop"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--launch", action="store_true", help="Open Codex, wait for startup, repair once and exit")
    args = parser.parse_args()
    if args.launch:
        subprocess.Popen(["explorer.exe", "shell:AppsFolder\\OpenAI.Codex_2p2nqsd0c76g0!App"])
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [c.c_void_p, w.BOOL, w.LPCWSTR]
    kernel.CreateMutexW.restype = w.HANDLE
    kernel.CreateEventW.argtypes = [c.c_void_p, w.BOOL, w.BOOL, w.LPCWSTR]
    kernel.CreateEventW.restype = w.HANDLE
    kernel.OpenEventW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
    kernel.OpenEventW.restype = w.HANDLE
    kernel.SetEvent.argtypes = [w.HANDLE]
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    if args.stop:
        event = kernel.OpenEventW(2, False, STOP)
        if event:
            kernel.SetEvent(event)
            kernel.CloseHandle(event)
        return
    mutex = kernel.CreateMutexW(None, False, MUTEX)
    if not mutex:
        raise c.WinError(c.get_last_error())
    if c.get_last_error() == 183:
        kernel.CloseHandle(mutex)
        return
    event = kernel.CreateEventW(None, True, False, STOP)
    if not event:
        kernel.CloseHandle(mutex)
        raise c.WinError(c.get_last_error())
    spec = importlib.util.spec_from_file_location("pet_repair", ROOT / "fix-pet-click-through.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    status_path = ROOT / "pet-window-backups" / "watcher-status.json"
    status_path.parent.mkdir(exist_ok=True)

    def record(result):
        status_path.write_text(json.dumps({"watcher_pid": os.getpid(),
            "time": datetime.datetime.now().astimezone().isoformat(), **result}, indent=2), encoding="utf-8")

    record({"status": "started"})
    try:
        # One startup grace period; no repeated checks or resident worker.
        if args.launch and kernel.WaitForSingleObject(event, 8000) != 258:
            record({"status": "cancelled"})
            return
        try:
            result = module.repair(allow_missing=True)
        except Exception as error:
            result = {"status": "error", "message": str(error)}
        if result.get("status") == "waiting":
            result["status"] = "skipped_no_unique_pet"
        record({**result, "mode": "one-shot", "finished": True})
    finally:
        kernel.CloseHandle(event)
        kernel.CloseHandle(mutex)


if __name__ == "__main__":
    main()
