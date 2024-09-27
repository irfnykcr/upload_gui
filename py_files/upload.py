from functools import partial
from json import load
from random import randint
from shutil import rmtree
from threading import Thread
from time import perf_counter_ns, time, sleep
from cryptography.fernet import Fernet
from os import listdir, mkdir, path
from deflate import zlib_compress
from requests import post
from sys import argv
print("starting..")
with open(r"./config/config.json", "r") as f:
	j = load(f)
	UNIQUE_KEY = j['api_key']
	MAX_THREADS = j['max_threads'] # ±1
	MAX_RETRY = j['max_retry']
	RETRIES = 0
	TMP_DIR = j['tmp_dir']
F_LOC = fr"{argv[1]}"
F_NAME = argv[2]
F_ABOUT = argv[3]
F_CATEGORY = argv[4]
F_TYPE = argv[5]
F_PRIVATE = argv[6]

THREADS_NOW = 0
REEL_HASH = ""
FSIZE = path.getsize(F_LOC)
def add_url(urls:str):
	global UNIQUE_KEY
	global REEL_HASH
	if type(REEL_HASH) == bytes:
		REEL_HASH = REEL_HASH.decode("utf-8")
	data_j = {"weburl":REEL_HASH, "urls":urls}
	r = post("https://api.turkuazz.online/v1/upload/add_url", headers={"api-key":UNIQUE_KEY}, json=data_j)
	if r.status_code != 200:
		return False, r.content
	return r.content
def add_file():
	global F_NAME
	global F_ABOUT
	global F_CATEGORY
	global F_TYPE
	global F_PRIVATE
	global FSIZE
	global UNIQUE_KEY
	data = {"name":F_NAME, "size":FSIZE, "about":F_ABOUT, "category":F_CATEGORY, "type":F_TYPE, "private":F_PRIVATE}
	r = post("https://api.turkuazz.online/v1/upload/add_file", headers={"api-key":UNIQUE_KEY}, json=data)
	if r.status_code != 200:
		return False, r.content
	return r.content
def getkey():
	global UNIQUE_KEY
	r = post("https://api.turkuazz.online/v1/upload/getkey", headers={"api-key":UNIQUE_KEY})
	if r.status_code != 200:
		return False, r.content
	return r.content
def abort():
	global GENHASH
	rmtree(fr"{TMP_DIR}/{GENHASH}")
	exit()



ferkey = getkey()
if ferkey[0] == False:
	print(f"something went wrong while getting ferkey! {ferkey[1]}")
	abort()
FER = Fernet(ferkey)
def slice():
	global GENHASH
	global F_LOC
	global TMP_DIR
	global FSIZE
	outfile= fr"{TMP_DIR}/{GENHASH}"

	totalnumber = (FSIZE/1024/1024)/3
	if totalnumber > int(totalnumber):
		totalnumber = int(totalnumber)+1
	mkdir(outfile)
	n = 0
	tlist = []
	def wFile(filename:int, data:bytes):
		data = FER.encrypt(data)
		fsize = len(data)
		filename_len = 5-len(str(filename))
		if filename_len > 0:
			filename = "0"*filename_len + str(filename)
		with open(fr"{outfile}/{filename}_{fsize}.trkz", "wb") as f:
			f.write(zlib_compress(data, 6))
	with open(F_LOC, "rb") as f:
		for u in iter(partial(f.read, 3072001), b''):
			if n % 10 == 0:
				print(f"{n}/{totalnumber}")
			if n % 1000 == 0:
				for th in tlist:
					th.start()
				for th in tlist:
					th.join()
				tlist = []
			tlist.append(Thread(target=wFile, args=(n,u,)))
			n+=1
		for th in tlist:
			print(f"<1000 tamamlanıyor..")
			th.start()
		for th in tlist:
			th.join()
	return True

GENHASH = str(round(time() * 10000)) # unique name
slice()
print("sliced!")


REEL_HASH = add_file()
if REEL_HASH[0] == False:
	print(f"mysql error! {REEL_HASH[1]}")
	abort()
print("mysql okay!")

URLS_LIST = []
def upfunc(name:str) -> list:
	global UNIQUE_KEY
	global URLS_LIST
	global TARGET_LEN
	global START_DATE
	global THREADS_NOW
	global MAX_THREADS
	global RETRIES
	global MAX_RETRY
	while THREADS_NOW > MAX_THREADS:
		sleep(randint(1,3))
	THREADS_NOW += 1
	file = fr"{TMP_DIR}/{GENHASH}/{name}"
	print(f"+ {name}")
	with open(file, "rb") as f:
		data = f.read()
	url = post("https://api.turkuazz.online/v1/upload/upfile", headers={"api-key": UNIQUE_KEY}, data=data)
	THREADS_NOW -= 1
	if url.status_code != 200:
		if RETRIES >= MAX_RETRY:
			print(f"something went wrong while uploading file! exitting. {url.content} {url.status_code}")
			abort()
		RETRIES += 1
		print(f"something went wrong while uploading file! retrying.. {url.content} {url.status_code}")
		return upfunc(name)

	url = url.content.decode()
	url = url.split(",")
	
	x = name.replace(".trkz", "").split("_")
	fsize = x[1]
	fsira = int(x[0])
	url = [str(url[0]), int(url[1]), fsize, fsira]
	URLS_LIST.append(url)
	lenurllist = len(URLS_LIST)
	up_s = round(lenurllist/((perf_counter_ns()/10e8)-START_DATE), 2)
	print(f"- {name} --:: {lenurllist}/{TARGET_LEN} = {round((lenurllist/TARGET_LEN)*100, 2)}% --:: {up_s}up/s --:: kalan ~= {round(((TARGET_LEN-lenurllist)/up_s)/60, 2)}dk")
	return

listdir_genhash = listdir(fr"{TMP_DIR}/{GENHASH}")
TARGET_LEN = len(listdir_genhash)
START_DATE = perf_counter_ns()/10e8

threads = []
for i in listdir_genhash:
	threads.append(Thread(target=upfunc, args=(i,)))

[th.start() for th in threads]
[th.join() for th in threads]

print("upload okay! making adjustments..")
URLS_LIST.sort(key=lambda x: x[-1])
urls = [x[:-1] for x in URLS_LIST]

r = add_url(str(urls).replace(" ", ""))
if r[0] == False:
	print(f"something went wrong while adding urls! {r[1]}")
	abort()
print("all is okay!")
rmtree(fr"{TMP_DIR}/{GENHASH}")
print(f"url-id: {REEL_HASH}")