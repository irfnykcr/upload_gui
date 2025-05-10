from functools import partial
from json import load
from random import randint
from threading import Thread
from time import perf_counter_ns, sleep
from traceback import print_exc
from cryptography.fernet import Fernet
from os import path, _exit
from deflate import zlib_compress
from requests import post
from py_files import generate_thumb


#TODO: ADD CHECKSUM ON SERVER AND CLIENT SIDE
#TODO: test uploading from memory

def abort():
	global ABORT
	ABORT = 1
	global TMP_DIR
	global PRINT_CALLBACK
	PRINT_CALLBACK("aborting..")
	exit()
	_exit()
	return [0, "exit"]

def run(f_loc:str, f_name:str, f_about:str, f_category:str, f_type:str, f_private:str, print_callback=print):
	global ABORT
	ABORT = 0
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
	if ABORT: return 0, "abort signal"
	return __run()


def __run()->tuple[bool,str]:
	global ABORT
	if ABORT: print("!!!abort signal!!!");return False, "abort signal"
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
	global REEL_HASH
	global PRINT_CALLBACK
	PRINT_CALLBACK("starting..")


	THREADS_NOW = 0
	REEL_HASH = ""
	def add_url(urls:str) -> tuple[bool, bytes]:
		global ABORT
		if ABORT: print("!!!abort signal!!!");return False, b"abort signal"
		global UNIQUE_KEY
		global REEL_HASH
		if type(REEL_HASH) == bytes:
			REEL_HASH = REEL_HASH.decode("utf-8")
		data_j = {"weburl":REEL_HASH, "urls":urls}
		r = post("https://api.turkuazz.vip/v1/upload/add_url", headers={"api-key":UNIQUE_KEY}, json=data_j)
		if r.status_code != 200 or not r.content:
			return False, r.content
		return True, r.content
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
	def getkey() -> tuple[bool, bytes]:
		global ABORT
		if ABORT: print("!!!abort signal!!!");return (False, b"abort signal")
		global UNIQUE_KEY
		r = post("https://api.turkuazz.vip/v1/upload/getkey", headers={"api-key":UNIQUE_KEY})
		if r.status_code != 200:
			return (False, r.content)
		return (True, r.content)

	ferkey_getkey = getkey()
	if not ferkey_getkey[0]:
		PRINT_CALLBACK(f"something went wrong while getting ferkey! {ferkey_getkey[1]}")
		return abort()
	else:
		ferkey:bytes = ferkey_getkey[1]
	global FER
	FER = Fernet(ferkey)

	if ABORT: print("!!!abort signal!!!");return False, "abort signal"

	PRINT_CALLBACK("sliced!")

	REEL_HASH = add_file()
	if REEL_HASH[0] == False:
		PRINT_CALLBACK(f"mysql error! {REEL_HASH[1]}")
		return abort()
	PRINT_CALLBACK("mysql okay!")

	URLS_LIST = []
	def upfunc(data:bytes, fsira:int, fsize:int):
		global ABORT
		if ABORT: print("!!!abort signal!!!");return [0, "abort signal"]
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
			if ABORT: print("!!!abort signal!!!");return [0, "abort signal"]
			sleep(randint(1,3))
		if ABORT: print("!!!abort signal!!!");return [0, "abort signal"]
		THREADS_NOW += 1

		try:
			url = post("https://api.turkuazz.vip/v1/upload/upfile", headers={"api-key": UNIQUE_KEY}, data=data)
			THREADS_NOW -= 1
			if url.status_code != 200:
				if RETRIES >= MAX_RETRY:
					PRINT_CALLBACK(f"something went wrong while uploading file! exitting. {url.content} {url.status_code}")
					return abort()
				RETRIES += 1
				PRINT_CALLBACK(f"something went wrong while uploading file! retrying.. {url.content} {url.status_code}")
				if ABORT: print("!!!abort signal!!!");return [0, "abort signal"]
				return upfunc(data, fsira, fsize)
		except Exception as e:
			print_exc()
			PRINT_CALLBACK(f"something went wrong while uploading file! exitting. {e}")
			abort()
			return [0, "abort signal"]


		url = url.content.decode()
		url = url.split(",")

		url = [str(url[0]), int(url[1]), fsize, fsira]
		URLS_LIST.append(url)
		lenurllist = len(URLS_LIST)
		up_s = round(lenurllist/((perf_counter_ns()/10e8)-START_DATE), 2)
		PRINT_CALLBACK(f"- {fsira} --:: {lenurllist}/{TARGET_LEN}={round((lenurllist/TARGET_LEN)*100, 2)}% --:: {up_s}up/s --:: kalan ~= {round(((TARGET_LEN-lenurllist)/up_s)/60, 2)}dk")
		return


	TARGET_LEN = (FSIZE/1024/1024)/3
	START_DATE = perf_counter_ns()/10e8
	thread_list:list[Thread] = []
	fsira = 0
	with open(F_LOC, "rb") as target_file:
		for u in iter(partial(target_file.read, 3072001), b''):
			ec_data = FER.encrypt(u)
			fsize = len(ec_data)
			ec_data = zlib_compress(ec_data, 6)
			thread_list.append(Thread(target=upfunc, args=(ec_data,fsira,fsize)))
			fsira+=1
			if len(thread_list) > MAX_THREADS:
				[th.start() for th in thread_list]
				[th.join() for th in thread_list]
				thread_list = []
	if len(thread_list) > 0:
		print(f"last ones.. lenthread_list`{len(thread_list)}`")
		[th.start() for th in thread_list]
		[th.join() for th in thread_list]

	PRINT_CALLBACK("upload okay! making adjustments..")
	URLS_LIST.sort(key=lambda x: x[-1])
	urls = [x[:-1] for x in URLS_LIST]

	r = add_url(str(urls).replace(" ", ""))
	if r[0] == False:
		PRINT_CALLBACK(f"something went wrong while adding urls! {r[1]}")
		return abort()
	PRINT_CALLBACK("all is okay!")
	PRINT_CALLBACK(f"url-id: {REEL_HASH}")
	if ABORT: print("!!!abort signal!!!");return False, "abort signal"
	# # generating thumbnail
	# if (F_TYPE == "video") or (F_TYPE == "image"):
	# 	PRINT_CALLBACK(f"making thumb for {REEL_HASH}")
	# 	if generate_thumb.start(str(F_LOC), str(REEL_HASH), str(F_TYPE), ) != True:
	# 		PRINT_CALLBACK("!!! thumbnail not generated")
	# 		return False, "thumbnail error"
	# PRINT_CALLBACK("thumbnail generated and uploaded.")
	return True, "everything ok"