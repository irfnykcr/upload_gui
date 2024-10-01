
# file to text
This project is to chunk, encrypt, compress and upload files.
It will automatically create a folder with given input under the output directory.
Make sure to open up space at least equal to the file that you will upload.

Added downloading & generating thumbnail functionality too.

## why

I wanted to upload files to my website using python.
Any user can upload to their account with their api key.
Every user has different encryption key. Everything stored in a database, encrypted.
Users can download their files later with their api key.

## Run Locally

Go to the project directory
```bash
cd upload_cli
```

Add required modules and libraries
```bash
python -m pip install -r requirements.txt
```

Configure the script && Change the key
```bash
cd config
vim config.json
*make changes*
cd ..
```

Run the script
```bash
#for uploading
cd py_files
python upload.py <location:path> <name:str> <about:str> <category:str> <type:str:"photo"||"video"||"text"||"other"> <is_private:bool>
i.e:
python upload.py "C:/Users/user/Desktop/file.7z" "file.7z" "it is a 7z file" "main/" "other" "1"
```
```bash
#for downloading
cd py_files
python download.py <web-id:int||url:str>
i.e:
python download.py 664037273680
```
```bash
#for generating thumbnail
cd py_files
python generate_thumb.py <location:path> <uniuqe name:str> <ftype:str:"photo"||"video">
i.e:
python generate_thumb.py "C:/Users/user/Desktop/myvideo.mp4" "myvideo.mp4_pics" "video"
```
Or start the gui
```bash
python gui.py
```
### using with pyinstaller exe convertion
"setup.bat" script can be used for generating .exe files.

This means config.json should be changed accordingly.
```txt
"cmd_gen": "py_files/generate_thumb.exe",
"cmd_upload": "py_files/upload.exe",
"cmd_download": "py_files/download.exe"
```