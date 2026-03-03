import os
import subprocess
import platform
import shutil

def find_msvc_libs():
    vswhere = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    result = subprocess.run([vswhere, "-latest", "-property", "installationPath"], capture_output=True, text=True)
    vs_path = result.stdout.strip()
    
    msvc_tools = os.path.join(vs_path, "VC", "Tools", "MSVC")
    version = sorted(os.listdir(msvc_tools))[-1]
    msvc_lib = os.path.join(msvc_tools, version, "lib", "x64")
    
    sdk_root = r"C:\Program Files (x86)\Windows Kits\10\Lib"
    sdk_version = sorted(os.listdir(sdk_root))[-1]
    ucrt_lib = os.path.join(sdk_root, sdk_version, "ucrt", "x64")
    um_lib = os.path.join(sdk_root, sdk_version, "um", "x64")
    
    return msvc_lib, ucrt_lib, um_lib

def link(obj_file, exe_file):
    cmd = ["clang", obj_file, "-o", exe_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Linking failed")