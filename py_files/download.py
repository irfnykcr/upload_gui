from json import load
from requests import post
from os import _exit
from threading import Thread 
from time import perf_counter_ns, time

ABORT = 0
def abort():
	global ABORT
	ABORT = 1
	global PRINT_CALLBACK
	PRINT_CALLBACK("aborting..")
	exit()
	_exit()

def run(weburl, outdir="", print_callback=print):
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	global WEBURL
	global OUTDIR
	global UNIQUE_KEY
	global MAX_RETRY
	global RETRIES
	global NAME
	global TMP_DIR
	global MAX_THREADS
	global PRINT_CALLBACK

	WEBURL = weburl
	with open(r"./config/config.json", "r") as f:
		j = load(f)
		UNIQUE_KEY = j['api_key']
		MAX_THREADS = j['max_threads'] # ±1
		MAX_RETRY = j['max_retry']
		RETRIES = 0
		TMP_DIR = j['tmp_dir']

	PRINT_CALLBACK = print_callback
	
	if outdir == "":
		PRINT_CALLBACK("no outdir given. using outdir from config.")
		
		OUTDIR = j['outdir']
	else:
		OUTDIR = outdir
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	return __run()

def __run():
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	global UNIQUE_KEY
	global DONE
	global TOTAL
	global DATALIST
	global TIME_STARTED
	global MAX_RETRY
	global RETRIES
	global WEBURL
	global NAME
	global PRINT_CALLBACK

	PRINT_CALLBACK("starting..")

	def getfile_info():
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global WEBURL
		global UNIQUE_KEY
		r = post(f"https://api.turkuazz.vip/v1/download/getfile_info", headers={"api-key":UNIQUE_KEY}, json={"weburl":WEBURL})
		if r.status_code != 200:
			return False, r.content
		return eval(r.content)

	file_info = getfile_info()
	if file_info[0] == False:
		PRINT_CALLBACK(f"something went wrong while getting file info! {file_info[1]}")
		return abort()
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	NAME = file_info[0]
	URLS = eval(file_info[1])
	TOTAL = len(URLS)
	def download_chunk(url, n):
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global UNIQUE_KEY
		global DONE
		global TOTAL
		global DATALIST
		global TIME_STARTED
		global MAX_RETRY
		global RETRIES
		global WEBURL
		global PRINT_CALLBACK
		try:
			PRINT_CALLBACK(f"+ {n}")
			r = post(f"https://api.turkuazz.vip/v1/download/get_chunk", headers={"api-key":UNIQUE_KEY}, json={"url":url, "weburl":WEBURL})
			data = r.content
			if r.status_code != 200:
				if RETRIES >= MAX_RETRY:
					PRINT_CALLBACK(f"something went wrong while uploading file! exitting. {r.content} {r.status_code}")
					return abort()
				RETRIES += 1
				PRINT_CALLBACK(f"something went wrong with {n} - post, retrying..",r.status_code, r.content)
				return download_chunk(url, n)
			DATALIST.append((n,data))
			DONE+=1
			up_s = round(DONE/((perf_counter_ns()/10e8)-TIME_STARTED), 2)
			PRINT_CALLBACK(f"- {n} --:: downloaded {round((DONE/TOTAL)*100,2)}% --:: {DONE}/{TOTAL} --:: {up_s}up/s --:: kalan ~= {round(((TOTAL-DONE)/up_s)/60, 2)}dk")
		except Exception as e:
			PRINT_CALLBACK(f"something went wrong with {n}, trying again.", e)
			return download_chunk(url, n)

	threads = []
	n = 0
	for url in URLS:
		n+=1
		threads.append(Thread(target=download_chunk, args=(url, n)))
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	n = 0
	DONE = 0
	DATALIST = []
	STARTED_THREAD = []
	PRINT_CALLBACK("starting threads..")
	TIME_STARTED = perf_counter_ns()/10e8

	def write_downloaded():
		global ABORT
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		global DATALIST
		global WEBURL
		global NAME
		global OUTDIR
		global PRINT_CALLBACK
		DATALIST.sort(key=lambda x: x[0])
		with open(fr"{OUTDIR}/{WEBURL}.{NAME}", "ab") as f:
			for data in DATALIST:
				lendata = len(data[1])
				PRINT_CALLBACK(f"~ writing: {data[0]} --:: size: {lendata}")
				if lendata > 3072001:
					f.write(data[1][:3072001])
					log_fname = fr"{TMP_DIR}/{WEBURL}.{NAME}.{int(time())}.log"
					with open(log_fname, "ab") as fl:
						PRINT_CALLBACK(f"found excess data. writing into: {log_fname}")
						fl.write(data[1][3072001:])
				else:
					f.write(data[1])
		DATALIST = []

	for t in threads:
		n+=1
		t.start()
		STARTED_THREAD.append(t)
		if n % MAX_THREADS == 0:
			if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
			for th in STARTED_THREAD:
				th.join()
			write_downloaded()
			STARTED_THREAD = []
	lenkalan = len(STARTED_THREAD)
	PRINT_CALLBACK(f"finishing last ones.. len:{lenkalan}")
	if lenkalan > 0:
		for th in STARTED_THREAD:
			th.join()
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		write_downloaded()
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	PRINT_CALLBACK("all is okay!")
	return True