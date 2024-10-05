
del gui2.exe
pyinstaller --onefile --clean gui2.py
cp dist/gui2.exe gui2.exe
rm -rf dist
rm -rf build
rm -f gui2.spec

IF "%~1"=="1" GOTO skip :: only build the GUI

cd py_files

del upload.exe
pyinstaller --onefile --clean upload.py
cp dist/upload.exe upload.exe
rm -rf dist
rm -rf build
rm -f upload.spec

del download.exe
pyinstaller --onefile --clean download.py
cp dist/download.exe download.exe
rm -rf dist
rm -rf build
rm -f download.spec

del generate_thumb.exe
pyinstaller --onefile --clean generate_thumb.py
cp dist/generate_thumb.exe generate_thumb.exe
rm -rf dist
rm -rf build
rm -f generate_thumb.spec

cd ..

:skip
echo "--!!-- end."