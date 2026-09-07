"""Reset only persisted pet bounds while the Codex desktop app is closed."""
import argparse
import datetime
import json
import pathlib
import subprocess


def reset_bounds(state):
    result = dict(state)
    result.pop("electron-avatar-overlay-bounds", None)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    state_path = pathlib.Path.home() / ".codex" / ".codex-global-state.json"
    original = state_path.read_bytes()
    state = json.loads(original.decode("utf-8-sig"))
    result = reset_bounds(state)
    if args.check:
        assert {k: v for k, v in state.items() if k != "electron-avatar-overlay-bounds"} == result
        print("Check passed: only pet window bounds would be removed.")
        return
    probe = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command",
         "$ErrorActionPreference='Stop'; Get-CimInstance Win32_Process | "
         "Where-Object { $_.Name -match '^(ChatGPT|Codex)\\.exe$' } | "
         "Select-Object ProcessId,Name | ConvertTo-Json -Compress"],
        capture_output=True, text=True, check=True,
    )
    if probe.stdout.strip():
        raise RuntimeError("Exit Codex/ChatGPT completely, then run this tool again. No files changed.")
    if state == result:
        print("No saved pet bounds exist. Nothing changed.")
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = pathlib.Path(__file__).resolve().parent / "pet-window-backups" / stamp
    backup.mkdir(parents=True, exist_ok=False)
    (backup / "codex-global-state.json").write_bytes(original)
    pet_path = pathlib.Path.home() / ".codex" / "pets" / "xiselius"
    for name in ("pet.json", "spritesheet.webp"):
        source = pet_path / name
        if source.is_file():
            (backup / name).write_bytes(source.read_bytes())
    if state_path.read_bytes() != original:
        raise RuntimeError("State changed during backup. Aborted without changing configuration.")
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = state_path.with_name(state_path.name + ".pet-repair-" + stamp)
    temporary.write_bytes(encoded)
    temporary.replace(state_path)
    assert json.loads(state_path.read_text(encoding="utf-8")) == result
    print("Pet window position reset. Start Codex and test clicking/dragging.")
    print("Backup:", backup)
    print("Pet artwork and all other settings were preserved.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("NOT COMPLETED:", error)
        raise SystemExit(1)
