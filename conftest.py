import platform

not_macOS = platform.system() != 'Darwin'

collect_ignore = ["hook-keyring.backend.py"] + [
    'keyring/backends/macOS/api.py'
] * not_macOS

def windowsos_api_ignore():
    try:
        ctypes.windll
        return False
    except Exception:
        return True


collect_ignore.extend(['keyring/backends/windowsOS/api.py'] * windowsos_api_ignore())