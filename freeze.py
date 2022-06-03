# See https://pyinstaller.org/en/stable/usage.html#running-pyinstaller-from-python-code

import identity

import PyInstaller.__main__

PyInstaller.__main__.run([
    '--onefile',
    '--windowed',
    f'--name=hypercube-{identity.VERSION}',
    '--hidden-import=pyi_splash',
    '--splash=build\\splash.jpg',
    'main.py',
])
