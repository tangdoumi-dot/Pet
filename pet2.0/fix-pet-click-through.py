"""One-shot workaround for openai/codex#43200. Does not edit app files."""
import argparse
import ctypes as c
import json
from ctypes import wintypes as w

LAYERED = 0x80000
TOOLWINDOW = 0x80
TOPMOST = 0x8


def repair(check=False, restore=False, allow_missing=False):
    user = c.WinDLL("user32", use_last_error=True)
    kernel = c.WinDLL("kernel32", use_last_error=True)
    user.GetWindowLongW.argtypes = [w.HWND, c.c_int]
    user.GetWindowLongW.restype = c.c_long
    user.SetWindowLongW.argtypes = [w.HWND, c.c_int, c.c_long]
    user.SetWindowLongW.restype = c.c_long
    user.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
    user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
    user.IsWindowVisible.argtypes = [w.HWND]
    user.SetWindowPos.argtypes = [w.HWND, w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.UINT]
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    user.EnumWindows.argtypes = [callback_type, w.LPARAM]
    candidates = []
    app_windows = []

    @callback_type
    def visit(hwnd, _):
        style = user.GetWindowLongW(hwnd, -20) & 0xFFFFFFFF
        pid = w.DWORD()
        user.GetWindowThreadProcessId(hwnd, c.byref(pid))
        process = kernel.OpenProcess(0x1000, False, pid.value)
        if not process:
            return True
        try:
            path = c.create_unicode_buffer(32768)
            length = w.DWORD(len(path))
            if not kernel.QueryFullProcessImageNameW(process, 0, path, c.byref(length)):
                return True
        finally:
            kernel.CloseHandle(process)
        executable = path.value.lower()
        if "\\windowsapps\\openai.codex_" not in executable or not executable.endswith("\\app\\chatgpt.exe"):
            return True
        app_windows.append(hwnd)
        if not user.IsWindowVisible(hwnd) or style & (TOOLWINDOW | TOPMOST) != TOOLWINDOW | TOPMOST:
            return True
        rect = w.RECT()
        if user.GetWindowRect(hwnd, c.byref(rect)) and rect.right > rect.left and rect.bottom > rect.top:
            candidates.append((hwnd, pid.value, style))
        return True

    if not user.EnumWindows(visit, 0):
        raise c.WinError(c.get_last_error())
    if len(candidates) != 1:
        if allow_missing:
            return {"status": "waiting", "candidates": len(candidates), "app_running": bool(app_windows)}
        raise RuntimeError(f"Expected one visible Codex pet overlay; found {len(candidates)}. No changes made.")
    hwnd, pid, before = candidates[0]
    after = before | LAYERED if restore else before & ~LAYERED
    if not check and after != before:
        c.set_last_error(0)
        previous = user.SetWindowLongW(hwnd, -20, after)
        error = c.get_last_error()
        if not previous and error:
            raise c.WinError(error)
        # Recalculate the frame without moving, resizing, focusing, or reordering.
        if not user.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x37):
            user.SetWindowLongW(hwnd, -20, before)
            raise RuntimeError("Frame refresh failed; original style restored.")
    actual = user.GetWindowLongW(hwnd, -20) & 0xFFFFFFFF
    if not check and actual != after:
        raise RuntimeError("Codex changed the window style during repair. Retry with the pet visible.")
    return {"status": "changed" if actual != before else "unchanged",
            "window": hex(hwnd), "pid": pid, "before": hex(before),
            "after": hex(actual), "check_only": check, "layered": bool(actual & LAYERED)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    print(json.dumps(repair(check=args.check, restore=args.restore), indent=2))
    if not args.check:
        print("Original layered mode restored." if args.restore else "Workaround applied. Test clicking and dragging the pet.")
        print("This is temporary; run again if Codex recreates the pet window.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("NOT COMPLETED:", error)
        raise SystemExit(1)
