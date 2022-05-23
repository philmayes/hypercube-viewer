# See https://pyinstaller.org/en/stable/usage.html#running-pyinstaller-from-python-code

import PyInstaller.__main__

PyInstaller.__main__.run([
    '--onefile',
    '--windowed',
    '--name=hypercube',
    '--hidden-import=pyi_splash',
    '--splash=build\\splash.jpg',
    'main.py',
])
