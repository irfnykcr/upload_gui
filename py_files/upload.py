from functools import partial
from json import load
from random import randint
from shutil import rmtree
from subprocess import PIPE, Popen
from threading import Thread
from time import perf_counter_ns, time, sleep
from cryptography.fernet import Fernet
from os import listdir, mkdir, path, _exit
from deflate import zlib_compress
from requests import post
from py_files import generate_thumb

ABORT = 0

def abort():
	global ABORT
	ABORT = 1
	global GENHASH
	global TMP_DIR
	global PRINT_CALLBACK
	if path.exists(fr"{TMP_DIR}/{GENHASH}"):
		rmtree(fr"{TMP_DIR}/{GENHASH}")
	PRINT_CALLBACK("aborting..")
	exit()
	_exit()

def run(f_loc, f_name, f_about, f_category, f_type, f_private, print_callback=print):
	global F_NAME
	global F_ABOUT
	global F_CATEGORY
	global F_TYPE
	global F_PRIVATE
	global FSIZE
	global UNIQUE_KEY
	global F_LOC
	global TMP_DIR
	global MAX_THREADS
	global RETRIES
	global MAX_RETRY
	global PYTHON_VER
	global CMD_GEN
	global PRINT_CALLBACK
	with open(r"./config/config.json", "r") as f:
		j = load(f)
		UNIQUE_KEY = j['api_key']
		MAX_THREADS = j['max_threads'] # ±1
		MAX_RETRY = j['max_retry']
		PYTHON_VER = j['python']
		CMD_GEN = j['cmd_gen']
		RETRIES = 0
		TMP_DIR = j['tmp_dir']
	F_LOC = fr"{f_loc}"
	F_NAME = f_name
	F_ABOUT = f_about
	F_CATEGORY = f_category
	F_TYPE = f_type
	F_PRIVATE = f_private
	FSIZE = path.getsize(F_LOC)

	PRINT_CALLBACK = print_callback
	global ABORT
	if ABORT: return 0
	return __run()


def __run():
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	global F_NAME
	global F_ABOUT
	global F_CATEGORY
	global F_TYPE
	global F_PRIVATE
	global FSIZE
	global UNIQUE_KEY
	global F_LOC
	global TMP_DIR
	global MAX_THREADS
	global RETRIES
	global MAX_RETRY
	global PYTHON_VER
	global CMD_GEN
	global URLS_LIST
	global TARGET_LEN
	global START_DATE
	global THREADS_NOW
	global GENHASH
	global REEL_HASH
	global PRINT_CALLBACK
	PRINT_CALLBACK("starting..")


	THREADS_NOW = 0
	REEL_HASH = ""
	def add_url(urls:str):
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global UNIQUE_KEY
		global REEL_HASH
		if type(REEL_HASH) == bytes:
			REEL_HASH = REEL_HASH.decode("utf-8")
		data_j = {"weburl":REEL_HASH, "urls":urls}
		r = post("https://api.turkuazz.vip/v1/upload/add_url", headers={"api-key":UNIQUE_KEY}, json=data_j)
		if r.status_code != 200:
			return False, r.content
		return r.content
	def add_file():
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global F_NAME
		global F_ABOUT
		global F_CATEGORY
		global F_TYPE
		global F_PRIVATE
		global FSIZE
		global UNIQUE_KEY
		data = {"name":F_NAME, "size":FSIZE, "about":F_ABOUT, "category":F_CATEGORY, "type":F_TYPE, "private":F_PRIVATE}
		r = post("https://api.turkuazz.vip/v1/upload/add_file", headers={"api-key":UNIQUE_KEY}, json=data)
		if r.status_code != 200:
			return False, r.content
		return r.content
	def getkey():
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global UNIQUE_KEY
		r = post("https://api.turkuazz.vip/v1/upload/getkey", headers={"api-key":UNIQUE_KEY})
		if r.status_code != 200:
			return False, r.content
		return r.content

	ferkey = getkey()
	if ferkey[0] == False:
		PRINT_CALLBACK(f"something went wrong while getting ferkey! {ferkey[1]}")
		return abort()
	global FER
	FER = Fernet(ferkey)
	def slice():
		global FER
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global GENHASH
		global F_LOC
		global TMP_DIR
		global FSIZE
		global PRINT_CALLBACK
		outfile= fr"{TMP_DIR}/{GENHASH}"

		totalnumber = (FSIZE/1024/1024)/3
		if totalnumber > int(totalnumber):
			totalnumber = int(totalnumber)+1
		mkdir(outfile)
		n = 0
		tlist = []
		def wFile(filename:int, data:bytes):
			global ABORT
			if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
			global FER
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
					PRINT_CALLBACK(f"{n}/{totalnumber}")
				if n % 1000 == 0:
					for th in tlist:
						th.start()
					for th in tlist:
						th.join()
					tlist = []
				tlist.append(Thread(target=wFile, args=(n,u,)))
				n+=1
			PRINT_CALLBACK(f"<1000 tamamlanıyor..")
			if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
			for th in tlist:
				th.start()
			for th in tlist:
				th.join()
		return True

	GENHASH = str(round(time() * 10000)) # unique name
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	slice()
	PRINT_CALLBACK("sliced!")
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"

	REEL_HASH = add_file()
	if REEL_HASH[0] == False:
		PRINT_CALLBACK(f"mysql error! {REEL_HASH[1]}")
		return abort()
	PRINT_CALLBACK("mysql okay!")

	URLS_LIST = []
	def upfunc(name:str) -> list:
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global UNIQUE_KEY
		global URLS_LIST
		global TARGET_LEN
		global START_DATE
		global THREADS_NOW
		global MAX_THREADS
		global RETRIES
		global MAX_RETRY
		global PRINT_CALLBACK
		while THREADS_NOW > MAX_THREADS:
			sleep(randint(1,3))
		THREADS_NOW += 1
		file = fr"{TMP_DIR}/{GENHASH}/{name}"
		PRINT_CALLBACK(f"+ {name}")
		with open(file, "rb") as f:
			data = f.read()
		url = post("https://api.turkuazz.vip/v1/upload/upfile", headers={"api-key": UNIQUE_KEY}, data=data)
		THREADS_NOW -= 1
		if url.status_code != 200:
			if RETRIES >= MAX_RETRY:
				PRINT_CALLBACK(f"something went wrong while uploading file! exitting. {url.content} {url.status_code}")
				return abort()
			RETRIES += 1
			PRINT_CALLBACK(f"something went wrong while uploading file! retrying.. {url.content} {url.status_code}")
			if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
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
		PRINT_CALLBACK(f"- {name} --:: {lenurllist}/{TARGET_LEN}={round((lenurllist/TARGET_LEN)*100, 2)}% --:: {up_s}up/s --:: kalan ~= {round(((TARGET_LEN-lenurllist)/up_s)/60, 2)}dk")
		return





	listdir_genhash = listdir(fr"{TMP_DIR}/{GENHASH}")
	TARGET_LEN = len(listdir_genhash)
	START_DATE = perf_counter_ns()/10e8

	threads = []
	for i in listdir_genhash:
		threads.append(Thread(target=upfunc, args=(i,)))

	[th.start() for th in threads]
	[th.join() for th in threads]

	PRINT_CALLBACK("upload okay! making adjustments..")
	URLS_LIST.sort(key=lambda x: x[-1])
	urls = [x[:-1] for x in URLS_LIST]

	r = add_url(str(urls).replace(" ", ""))
	if r[0] == False:
		PRINT_CALLBACK(f"something went wrong while adding urls! {r[1]}")
		return abort()
	PRINT_CALLBACK("all is okay!")
	rmtree(fr"{TMP_DIR}/{GENHASH}")
	PRINT_CALLBACK(f"url-id: {REEL_HASH}")
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	# generating thumbnail
	if (F_TYPE == "video") or (F_TYPE == "image"):
		PRINT_CALLBACK(f"making thumb for {REEL_HASH}")
		if generate_thumb.start(str(F_LOC), str(REEL_HASH), str(F_TYPE), ) != True:
			PRINT_CALLBACK("!!! thumbnail not generated")
			return False
	PRINT_CALLBACK("thumbnail generated and uploaded.")
	return True