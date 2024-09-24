
# file to text

This project is to chunk, encrypt, compress and upload files.
It will automatically create a folder with given input under the output directory.
Make sure to open up space at least equal to file that you will upload.


## why

I wanted to upload files to my website using python.
Users can upload with their api so anyone can upload files to their accounts.
Every user has different encryption key. Everything stored in a database encrypted.


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
cd ..
```

Run the script
```bash
python main.py <location> <name> <about> <category> <type> <private:>
```
Example
```bash
python main.py "C:/Users/user/Desktop/file.7z" "file.7z" "it is a 7z file" "main/" "other" "1"
```