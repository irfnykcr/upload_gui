
# file to text
This project is to chunk, encrypt, compress and upload files.
It will automatically create a folder with given input under the output directory.
Make sure to open up space at least equal to the file that you will upload.

Added downloading functionality too.

## why

I wanted to upload files to my website using python.
Any user can upload to their account with their api.
Every user has different encryption key. Everything stored in a database encrypted.
Users can download their files later.

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
python upload.py <location> <name> <about> <category> <type:"photo"||"video"||"text"||"other"> <is_private:bool>
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
Or start the gui
```bash
python gui.py
```
