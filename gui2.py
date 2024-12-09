from datetime import datetime
from json import load
from subprocess import PIPE, Popen
from threading import Thread
from time import sleep, time
from uuid import uuid4
from requests import post
from webview import OPEN_DIALOG, create_window, start, settings, FOLDER_DIALOG
from os import getcwd

CURRENT_PATH = getcwd()
print(CURRENT_PATH)
with open(fr"{CURRENT_PATH}/config/config.json", "r") as f:
	j = load(f)
	PYTHON_VER = j['python']
	CMD_UPLOAD = fr"{j['cmd_upload']}"
	CMD_DOWNLOAD = fr"{j['cmd_download']}"
	CMD_GEN = fr"{j['cmd_gen']}"
	API_KEY = j['api_key']
	PORT = j['port']
	DEFAULT_OUTDIR = j['outdir']
	VLC_PATH = j['vlc']
	VLC_PORT = j['vlc_port']
	VLC_HTTP_PASS = j['vlc_http_pass']
	CDN_URL = j['cdn_url']
ACCEPTED_CHR = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZıĞğÜüŞşİÖöÇç-,._()!+-[]{} ")
VIDEO_EXT = [".mp4", ".mov", ".avi", ".wmv", ".mkv", ".webm", ".flv", ".ts"]
PHOTO_EXT = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
TXT_EXT = [".txt"]

CATEGORIES = []
CATEGORIES_LIST = []
FILES_LIST = []
CURRENT_VIDEO = None
width = 1200
height = 860
settings = {
  'ALLOW_DOWNLOADS': False,
  'ALLOW_FILE_URLS': True,
  'OPEN_EXTERNAL_LINKS_IN_BROWSER': False,
  'OPEN_DEVTOOLS_IN_DEBUG': True
}


def changeconsole(msg):
	global WINDOW
	c = WINDOW.dom.get_element(".console")
	c.append(f"<p>{str(datetime.now()).split(' ')[1][:10]}> {msg}</p>")
	c = WINDOW.dom.get_element(".autoscroll") #checkbox
	if WINDOW.evaluate_js('document.querySelector(".autoscroll").checked'):
		WINDOW.evaluate_js('$(".console").scrollTop(999999);')
	# WINDOW.evaluate_js('$(".console").scrollTop(999999);')

def changegui(value:bool):
	global WINDOW
	elements = [".header-upload", ".header-download", ".header-logo", ".header-files"]
	for element in elements:
		WINDOW.dom.get_element(element).style["disabled"] = value
		if value:
			WINDOW.dom.get_element(element).style["pointer-events"] = "none"
			WINDOW.dom.get_element(element).style["cursor"] = "not-allowed"
		else:
			WINDOW.dom.get_element(element).style["pointer-events"] = "all"
			WINDOW.dom.get_element(element).style["cursor"] = "pointer"

def abort(return_msg:dict):
	changegui(False)
	return return_msg

def make_request(url:str, json:dict, msg:str):
	global API_KEY
	try:
		r = post(url, headers={"api-key":API_KEY}, json=json)
		rc = r.content
		print(f"{datetime.now()} // made request:",msg,rc)
		return rc
	except Exception as e:
		print(f"{datetime.now()} // failed to make request:",msg,e)
		return None

def play(weburl:str):
	global VLC_PATH
	global VLC_PORT
	global VLC_HTTP_PASS
	global CURRENT_VIDEO
	global CDN_URL
	if CURRENT_VIDEO != None:
		print("already playing a vid")
		return False
	CURRENT_VIDEO = weburl
	def abort_vlc():
		CURRENT_VIDEO = None
		return "aborted"
	try:
		r = post("https://api.turkuazz.vip/v1/activity/currentsec", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		r = int(eval(r.decode("utf-8")))
	except:
		print("failed to get currentsec")
		r = 0
	# print(r,VLC_PORT,VLC_HTTP_PASS,url)
	url = CDN_URL + weburl
	
	command = [VLC_PATH, 
		"--intf", "qt",
		"--start-time="+str(r), 
		"--extraintf", "http",
		"--http-port", str(VLC_PORT),
		"--http-password", str(VLC_HTTP_PASS),
		str(url)
	]

	proc = Popen(command)#, stdout=PIPE, stderr=PIPE)
	duration = -1
	retry = 0
	def get_info():
		try:
			response = post(f"http://localhost:{VLC_PORT}/requests/status.json", auth=("",VLC_HTTP_PASS))
			response.raise_for_status()
			return response.json()
		except:
			return None
	while duration == -1:
		data = get_info()
		if data == None:
			if retry > 10:
				print("failed to get duration")
				return abort_vlc()
			retry += 1
			sleep(0.05)
			continue
		else:
			duration = data['length']
	r = post("https://api.turkuazz.vip/v1/activity/updatesec", headers={"api-key":API_KEY}, json={"weburl":weburl,"current":0,"state":"starting"}).content
	if r == b"ok":
		print("updated starting")
	else:
		print("failed to update starting", r)
	currentstate = None
	currenttime = 0
	update_timeout = time()
	while True:
		data = get_info()
		if data == None:
			print(f"{currenttime}/{duration}, exit")
			Thread(target=make_request, args=("https://api.turkuazz.vip/v1/activity/updatesec",{"weburl":weburl,"current":currenttime,"state":"update_time"},"update_time")).start()
			return abort_vlc()
		state = data['state']
		ttime = data['time']
		if state == "stopped":
			print(f"{currenttime}/{duration}, ended")
			sleep(0.1)
			continue
		if time() - update_timeout > 5:
			Thread(target=make_request, args=("https://api.turkuazz.vip/v1/activity/updatesec",{"weburl":weburl,"current":ttime,"state":"update_time"},"update_time")).start()
			update_timeout = time()
		if currentstate == state or currenttime == ttime:
			sleep(0.1)
			continue
		if ttime == duration:
			#Thread(target=make_request, args=("https://api.turkuazz.vip/v1/activity/updatesec",{"weburl":weburl,"finished":1},"finished")).start()
			print("finished but didnt update. will worked on it later.")
		else:
			Thread(target=make_request, args=("https://api.turkuazz.vip/v1/activity/updatesec",{"weburl":weburl,"current":ttime,"state":state},"current")).start()
		
		currentstate = state
		if currentstate != "ended":
			currenttime = ttime 
		print(f"{currenttime}/{duration}, {currentstate}")
	return abort_vlc()
class Api:
	
	def echostuff(self,*msg):
		print([i for i in msg])
		return True
	def openvlc(self, weburl:str):
		Thread(target=play, args=(weburl,)).start()
		return True
	def changetitle(self, title:str):
		global WINDOW
		WINDOW.title = title
		return {'status': True}

	def open_file_dialog(self):
		global WINDOW
		result = WINDOW.create_file_dialog(
			OPEN_DIALOG, allow_multiple=True, file_types=('All files (*.*)',)
		)
		return {'files': result}
	
	def activities_finish_video(self, weburl):
		r = post("https://api.turkuazz.vip/v1/activity/finish_file", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		return str(r.decode("utf-8"))
	
	def activities_back_video(self, weburl):
		r = post("https://api.turkuazz.vip/v1/activity/back_file", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		return str(r.decode("utf-8"))
	
	def activities_remove_video(self, weburl):
		r = post("https://api.turkuazz.vip/v1/activity/remove_file", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		r = r.decode("utf-8")
		return str(r)

	def get_lastactivity(self):
		r = post("https://api.turkuazz.vip/v1/activity/lastactivies", headers={"api-key":API_KEY}).content
		return str(r.decode("utf-8"))
	
	def get_categories(self):
		global CATEGORIES
		return {'categories': CATEGORIES}
	def get_categories_list(self, catg:str=""):
		global CATEGORIES_LIST
		if catg == "":
			return {'categories': CATEGORIES_LIST}
		if catg[-1] == "/":
			catg = catg[:-1]
		catg = catg.split("/")
		if len(catg) == 1:
			return {'categories': [i for i in CATEGORIES_LIST[catg[0]]]}
		elif len(catg) == 2:
			return {'categories': [i for i in CATEGORIES_LIST[catg[0]][catg[1]]]}
		else:
			return {'categories': []}
	def get_files(self, category:str=""):
		global FILES_LIST
		if FILES_LIST == []:
			r:bytes = post("https://api.turkuazz.vip/v1/files/getfiles", headers={"api-key":API_KEY}).content
			FILES_LIST = eval(r.decode("utf-8"))
		if category == "":
			return {'files': FILES_LIST}
		elif category == "*lastest":
			f = FILES_LIST
			f.sort(key=lambda x: x[7], reverse=True)
			f = [[i[0],i[1],i[2],i[5]] for i in f][:15]
			return str(f)
		else:
			if category[-1] != "/":
				category = category + "/"
			_temp_ctg = []
			for i in FILES_LIST:
				if i[2] == category:
					_temp_ctg.append(i)
			_temp_ctg.sort(key=lambda x: x[0])
			return {'files': _temp_ctg}
	def searchinall(self, weburl:str):
		try:
			weburl = int(weburl)
		except:
			return {'file': None}
		global FILES_LIST
		if FILES_LIST == []:
			r = post("https://api.turkuazz.vip/v1/files/getfiles", headers={"api-key":API_KEY}).content
			FILES_LIST = eval(r.decode("utf-8"))
		for i in FILES_LIST:
			if i[0] == weburl:
				return {'file': i}
		return {'file': None}
	def download(self, weburl:str):
		global WINDOW
		global CMD_DOWNLOAD
		global PYTHON_VER
		changegui(True)
		changeconsole(f"downloading: {weburl}")
		weburl = ''.join(x for x in weburl if x.isdigit())
		OUTDIR = WINDOW.create_file_dialog(FOLDER_DIALOG)
		if OUTDIR == None:
			changeconsole("selected folder is invalid. using default from config.")
			OUTDIR = DEFAULT_OUTDIR
		if type(OUTDIR) == list or type(OUTDIR) == tuple or type(OUTDIR) == set:
			OUTDIR = OUTDIR[0]
		command = [PYTHON_VER,
			"-u",
			CMD_DOWNLOAD,
			str(weburl),
			str(OUTDIR)
		]
		changeconsole(command)
		proc = Popen(command, stdout=PIPE, text=True, bufsize=1)
		while True:
			line = proc.stdout.readline()
			changeconsole(line.strip())
			if not line:
				break
		changeconsole("you can close the window now.")
		return abort({'status': 'success'})
	
	def upload(self, items):
		global ACCEPTED_CHR
		global VIDEO_EXT
		global PHOTO_EXT
		global TXT_EXT
		global CATEGORIES
		global WINDOW
		global PYTHON_VER
		global CMD_GEN
		global CMD_UPLOAD
		changegui(True)
		changeconsole(f"items: {items}")
		FILE = items[0]

		about = items[2]
		accp = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!""#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ")
		for chr in about:
			if chr not in accp:
				changeconsole("fail1")
				return abort({'status': 'fail'})
		if len(about) > 500:
			changeconsole("fail2")
			return abort({'status': 'fail'})
		
		private = items[5]
		private = 1 if private == "private" else 0

		category = items[3]
		if category[-1] != "/":
			category = category + "/"
		if category not in CATEGORIES:
			changeconsole("fail3")
			return abort({'status': 'fail'})

		autocheck = (len(FILE) > 1)
		for ffile in FILE:
			changeconsole(f"now: {ffile}")
			if autocheck:
				fname = ffile.split("\\")[-1]
				ext = "." + fname.split(".")[-1]
				if ext in VIDEO_EXT:
					ftype = "video"
				elif ext in PHOTO_EXT:
					ftype = "photo"
				elif ext in TXT_EXT:
					ftype = "txt"
				else:
					ftype = "other"
			else:
				fname = items[1]
				ftype = items[4]
				if not (ftype == "photo" or ftype == "video" or ftype=="text"):
					ftype = "other"

			accp = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZıĞğÜüŞşİÖöÇç-,._()!+-[]{} ")
			for chr in fname:
				if chr not in accp:
					changeconsole("fail4")
					return abort({'status': 'fail'})
			len_fname = len(fname)
			if (len_fname < 2) or (len_fname > 100):
				changeconsole("fail5")
				return abort({'status': 'fail'})

			if (ftype == "video") or (ftype == "image"):
				random_name = fname + uuid4().hex[:5]
				command = [PYTHON_VER,
			   		"-u",
					CMD_GEN,
			   		str(ffile),
					str(random_name),
					str(ftype)
				]
				proc = Popen(command, stdout=PIPE, text=True, bufsize=1)
				changeconsole(command)
				while True:
					line = proc.stdout.readline()
					changeconsole(line.strip())
					if not line:
						break
				changeconsole(f"generated random name. {random_name}")
			changeconsole("thumbnail generated. uploading file..")
	
			command = [PYTHON_VER,
				"-u",
				CMD_UPLOAD,
				str(ffile),
				str(fname),
				str(about),
				str(category),
				str(ftype),
				str(private)
			]
			changeconsole(command)
			proc = Popen(command, stdout=PIPE, text=True, bufsize=1)
			while True:
				line = proc.stdout.readline()
				changeconsole(line.strip())
				if not line:
					break
			changeconsole(f"!!uploaded!! {fname}")
		changeconsole("you can close the window now.")
		return abort({'status': 'success'})
	
if __name__ == '__main__':
	try:
		r = post("https://api.turkuazz.vip/v1/upload/get_categories", headers={"api-key":API_KEY})
		CATEGORIES_LIST = r.json()
		CATEGORIES = []
		for i in CATEGORIES_LIST:
			CATEGORIES.append(f"{i}/")
			for k in CATEGORIES_LIST[i]:
				CATEGORIES.append(f"{i}/{k}/")
				for l in CATEGORIES_LIST[i][k]:
					CATEGORIES.append(f"{i}/{k}/{l}/")
		api = Api()
		api.get_files()
		# WINDOW = create_window('upload', fr"{CURRENT_PATH}/views/index.html?i=upload", js_api=api, width=width, height=height, resizable=False, text_select=True, background_color="#181818")
		WINDOW = create_window('upload', fr"{CURRENT_PATH}/views/index.html?i=files", js_api=api, width=width, height=height, resizable=True, text_select=True, background_color="#181818")
	except:
		WINDOW = create_window('upload', fr"{CURRENT_PATH}/views/noapi.html", width=width, height=height, resizable=True, text_select=False, background_color="#181818")
	start(http_port=PORT, gui="gtk", debug=True)