from json import load
import requests
from sys import argv
from threading import Thread 
from time import perf_counter_ns, time

print("starting..")

WEBURL = argv[1]
with open(r"./config/config.json", "r") as f:
	j = load(f)
	UNIQUE_KEY = j['api_key']
	MAX_THREADS = j['max_threads'] # ±1
	MAX_RETRY = j['max_retry']
	RETRIES = 0
	try:
		OUTDIR = argv[2]
	except:
		print("no outdir given. using outdir from config.")
		OUTDIR = j['outdir']
	TMP_DIR = j['tmp_dir']

THREADS_NOW = 0

def getfile_info():
	global WEBURL
	global UNIQUE_KEY
	r = requests.post(f"https://api.turkuazz.online/v1/download/getfile_info", headers={"api-key":UNIQUE_KEY}, json={"weburl":WEBURL})
	if r.status_code != 200:
		return False, r.content
	return eval(r.content)

file_info = getfile_info()
if file_info[0] == False:
	print(f"something went wrong while getting file info! {file_info[1]}")
	exit()
NAME = file_info[0]
URLS = eval(file_info[1])
TOTAL = len(URLS)
def download_chunk(url, n):
	global UNIQUE_KEY
	global DONE
	global TOTAL
	global DATALIST
	global TIME_STARTED
	global MAX_RETRY
	global RETRIES
	try:
		print(f"+ {n}")
		r = requests.post(f"https://api.turkuazz.online/v1/download/get_chunk", headers={"api-key":UNIQUE_KEY}, json={"url":url})
		data = r.content
		if r.status_code != 200:
			if RETRIES >= MAX_RETRY:
				print(f"something went wrong while uploading file! exitting. {r.content} {r.status_code}")
				exit()
			RETRIES += 1
			print(f"something went wrong with {n} - post, retrying..",r.status_code, r.content)
			return download_chunk(url, n)
		DATALIST.append((n,data))
		DONE+=1
		up_s = round(DONE/((perf_counter_ns()/10e8)-TIME_STARTED), 2)
		print(f"- {n} --:: downloaded {round((DONE/TOTAL)*100,2)}% --:: {DONE}/{TOTAL} --:: {up_s}up/s --:: kalan ~= {round(((TOTAL-DONE)/up_s)/60, 2)}dk")
	except Exception as e:
		print(f"something went wrong with {n}, trying again.", e)
		return download_chunk(url, n)

threads = []
n = 0
for url in URLS:
	n+=1
	threads.append(Thread(target=download_chunk, args=(url, n)))

n = 0
DONE = 0
DATALIST = []
STARTED_THREAD = []
print("starting threads..")
TIME_STARTED = perf_counter_ns()/10e8

def write_downloaded():
	global DATALIST
	global WEBURL
	global NAME
	DATALIST.sort(key=lambda x: x[0])
	with open(fr"{OUTDIR}/{WEBURL}.{NAME}", "ab") as f:
		for data in DATALIST:
			lendata = len(data[1])
			print(f"~ writing: {data[0]} --:: size: {lendata}")
			if lendata > 3072001:
				f.write(data[1][:3072001])
				log_fname = fr"{TMP_DIR}/{WEBURL}.{NAME}.{int(time())}.log"
				with open(log_fname, "ab") as fl:
					print(f"found excess data. writing into: {log_fname}")
					fl.write(data[1][3072001:])
			else:
				f.write(data[1])
	DATALIST = []

for t in threads:
	n+=1
	t.start()
	STARTED_THREAD.append(t)
	if n % MAX_THREADS == 0:
		for th in STARTED_THREAD:
			th.join()
		write_downloaded()
		STARTED_THREAD = []
lenkalan = len(STARTED_THREAD)
print(f"finishing last ones.. len:{lenkalan}")
if lenkalan > 0:
	for th in STARTED_THREAD:
		th.join()
	write_downloaded()

print("all is okay!")