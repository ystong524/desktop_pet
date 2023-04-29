@echo off
%userprofile%\py3_8\Scripts\pyinstaller.exe --noconsole --onefile --add-data "src*";"src" --icon baby.ico pet.py& pause