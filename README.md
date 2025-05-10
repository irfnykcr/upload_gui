
# file upload/download
This project is to chunk, encrypt, compress and upload files.
Has download & thumbnail generation functionality too.

## why

I wanted to upload files to my website using python.
Any user can upload to their account with their api key.
Everything stored in a database, encrypted.
Users can download their files later with their api key.

## Run Locally

Go to the project directory
```bash
cd upload_gui
```

Add required modules and libraries
```bash
python -m pip install -r requirements.txt
```

Configure the script && Change the key
```bash
cd config
cp config_example.json config.json
vim config.json
*make changes*
cd ..
```

Run the script
```bash
cd py_files
python gui.py
```