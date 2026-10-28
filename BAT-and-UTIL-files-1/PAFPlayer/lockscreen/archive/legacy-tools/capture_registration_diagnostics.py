"""Read-only PAFPlayer-specific Windows registration evidence (no repair)."""
from datetime import datetime, timezone
import json
import ctypes
from ctypes import wintypes
from pathlib import Path
import sqlite3
import subprocess
import sys
import winreg
from lockscreen_installer import WindowsBackend, PACKAGE_FAMILY, ps_args, ps_literal

ROOT = Path(__file__).resolve().parents[1]
CACHE = r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModel\StateRepository\Cache"

def registry(path):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, CACHE + "\\" + path) as key:
            values = {}
            for index in range(winreg.QueryInfoKey(key)[1]):
                name, value, kind = winreg.EnumValue(key, index)
                values[name] = value.hex() if isinstance(value, bytes) else value
            return {"present": True, "values": values}
    except FileNotFoundError:
        return {"present": False}

def main():
    backend = WindowsBackend()
    result = {"time": datetime.now(timezone.utc).isoformat(), "uacEnabled": backend.uac_enabled()}
    with sqlite3.connect("file:C:/ProgramData/Microsoft/Windows/AppRepository/StateRepository-Machine.srd?mode=ro", uri=True, timeout=2) as db:
        rows = db.execute("SELECT _PackageFamilyID,PackageFamilyName FROM PackageFamily WHERE PackageFamilyName IN (?,?)",
                          (PACKAGE_FAMILY, "Microsoft.WindowsCalculator_8wekyb3d8bbwe")).fetchall()
    result["families"] = [{"databaseId": i, "name": name,
                           "cacheData": registry("PackageFamily\\Data\\" + format(i, "x")),
                           "cacheIndex": registry("PackageFamily\\Index\\PackageFamilyName\\" + name)} for i, name in rows]
    lookup = ctypes.WinDLL("kernel32", use_last_error=True).GetPackagesByPackageFamily
    lookup.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.UINT), ctypes.c_void_p,
                       ctypes.POINTER(wintypes.UINT), ctypes.c_void_p]
    lookup.restype = wintypes.LONG
    for family in result["families"]:
        count, size = wintypes.UINT(0), wintypes.UINT(0)
        error = lookup(family["name"], ctypes.byref(count), None, ctypes.byref(size), None)
        family["nativeLookup"] = {"error": error, "count": count.value, "bufferCharacters": size.value}
    probe = Path(__file__).with_name("diagnose_activation.ps1")
    command = "& " + ps_literal(probe) + " -Activate -Arguments " + ps_literal("--verify " + str(ROOT / "tests" / "reports" / ("v510-diagnostic-publication-" + datetime.now().strftime("%Y%m%d%H%M%S") + ".json")))
    result["activation"] = json.loads(backend.run_ps(command))
    report = ROOT / "tests" / "reports" / ("v510-registration-diagnosis-" + datetime.now().strftime("%Y%m%d%H%M%S") + ".json")
    with report.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2)
    print(json.dumps(result, indent=2))
    print(report)

if __name__ == "__main__":
    main()
