from datetime import datetime
from json import load
from subprocess import Popen
from threading import Thread
from time import sleep, time
from traceback import print_exc
from requests import post
from webview import OPEN_DIALOG, create_window, start, settings, FOLDER_DIALOG, Window
from os import getcwd
from jellyfish import levenshtein_distance
from difflib import SequenceMatcher
from sys import argv
from py_files import download, upload

# TODO: MAKE ABORT WORK

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
	API_URL = j['api_url']
ACCEPTED_CHR = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZıĞğÜüŞşİÖöÇç-,._()!+-[]{} ")
VIDEO_EXT = [".mp4", ".mov", ".avi", ".wmv", ".mkv", ".webm", ".flv", ".ts"]
PHOTO_EXT = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
TXT_EXT = [".txt"]

CATEGORIES = []
CATEGORIES_LIST = []
FILES_LIST = []
CURRENT_VIDEO = None
width = 1385
height = 860
settings = {
  'ALLOW_DOWNLOADS': True,
  'ALLOW_FILE_URLS': True,
  'OPEN_EXTERNAL_LINKS_IN_BROWSER': False,
  'OPEN_DEVTOOLS_IN_DEBUG': True
}


def changeconsole(msg):
	global WINDOW
	c = WINDOW.dom.get_element(".console")
	if not c:
		return
	c.append(f"<p>{str(datetime.now()).split(' ')[1][:10]}> {msg}</p>")
	c = WINDOW.dom.get_element(".autoscroll") #checkbox
	if WINDOW.evaluate_js('document.querySelector(".autoscroll").checked'):
		WINDOW.evaluate_js('$(".console").scrollTop(999999);')
	# WINDOW.evaluate_js('$(".console").scrollTop(999999);')

def changegui(disable:bool):
	global WINDOW
	elements = [".header-upload", ".header-download", ".header-logo", ".header-files", ".header-edit"]
	for element in elements:
		selected_element = WINDOW.dom.get_element(element)
		if not selected_element:
			continue
		selected_element.style["disabled"] = disable
		if disable:
			selected_element.style["pointer-events"] = "none"
			selected_element.style["cursor"] = "not-allowed"
		else:
			selected_element.style["pointer-events"] = "all"
			selected_element.style["cursor"] = "pointer"

def abort(return_msg:dict) -> dict:
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

def is_similar(a:str, b:str):
	return (SequenceMatcher(None, a, b).ratio() - (levenshtein_distance(a,b)/max(len(a),len(b))))

def search_func(search_key:str):
	global FILES_LIST
	global CATEGORIES
	t = 0
	search_key = search_key.lower()
	searched_files = []
	searched_catg = []

	for i in CATEGORIES:
		s1 = is_similar(search_key, i.lower())
		if s1 > t:
			searched_catg.append(i)
	for i in FILES_LIST:
		# in name, category, about
		if search_key in i[1].lower() or search_key in i[2].lower() or search_key in i[5].lower():
			searched_files.append(i)
			continue
		s1 = is_similar(search_key, i[1].lower())
		s2 = is_similar(search_key, i[2].lower()) 
		s3 = is_similar(search_key, i[5].lower())
		if s1 > t or s2 > t or s3 > t:
			print(s1,s2,s3, i)
			searched_files.append(i)
	return searched_files, searched_catg
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
	def abort_vlc(proc_vlc:Popen[bytes]|None=None, retry=""):
		if isinstance(proc_vlc, Popen):
			proc_vlc.kill()
		global CURRENT_VIDEO
		CURRENT_VIDEO = None
		print(f"aborted: abort_vlc() w-kill/{proc_vlc!=None}")
		if retry != "":
			print(f"aborted, retry={retry}")
			return play(retry)
		return "aborted"
	try:
		currentsec = post(f"{API_URL}/activity/currentsec", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		currentsec = int(currentsec.decode("utf-8"))
	except:
		print("failed to get currentsec", )
		return abort_vlc(None, weburl)
		currentsec = 0
	# print(r,VLC_PORT,VLC_HTTP_PASS,url)
	url = CDN_URL + weburl

	command = [VLC_PATH,
		"--intf", "qt",
		"--start-time="+str(currentsec),
		"--extraintf", "http",
		"--http-port", str(VLC_PORT),
		"--http-password", str(VLC_HTTP_PASS),
		str(url)
	]

	proc_vlc = Popen(command)#, stdout=PIPE, stderr=PIPE)
	duration = -1
	retry = 0
	def get_info():
		try:
			response = post(f"http://127.0.0.1:{VLC_PORT}/requests/status.json", auth=("",VLC_HTTP_PASS))
			response.raise_for_status()
			return response.json()
		except:
			return None
	while duration == -1:
		data = get_info()
		if data == None:
			if retry > 10:
				print("failed to get duration")
				return abort_vlc(proc_vlc, weburl)
			retry += 1
			sleep(0.1)
			continue
		else:
			duration = data['length']
	r = post(f"{API_URL}/activity/updatesec", headers={"api-key":API_KEY}, json={"weburl":weburl,"current":currentsec,"state":"starting"}).content
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
			Thread(target=make_request, args=(f"{API_URL}/activity/updatesec",{"weburl":weburl,"current":currenttime,"state":"update_time"},f"update_time1 {currenttime}")).start()
			return abort_vlc(proc_vlc)
		state = data['state']
		ttime = data['time']
		if state == "stopped":
			print(f"{currenttime}/{duration}, ended")
			sleep(0.1)
			continue
		if time() - update_timeout > 5:
			update_timeout = time()
			if ttime == 0: continue
			Thread(target=make_request, args=(f"{API_URL}/activity/updatesec",{"weburl":weburl,"current":ttime,"state":"update_time"},f"update_time2 {ttime}")).start()
		if currentstate == state or currenttime == ttime:
			sleep(0.1)
			continue
		if ttime == duration:
			#Thread(target=make_request, args=(f"{API_URL}/activity/updatesec",{"weburl":weburl,"finished":1},"finished")).start()
			print("finished but didnt update. will worked on it later.")
		else:
			Thread(target=make_request, args=(f"{API_URL}/activity/updatesec",{"weburl":weburl,"current":ttime,"state":state},f"current {ttime}")).start()

		currentstate = state
		if currentstate != "ended":
			currenttime = ttime
		print(f"{currenttime}/{duration}, {currentstate}")
	return abort_vlc(proc_vlc)
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

	def isfirst_islast(self, weburl, category):
		global FILES_LIST
		try:
			samectg = [i[0] for i in FILES_LIST if i[2] == category]
			samectg.sort()
			return (samectg[0] == weburl, samectg[-1] == weburl)
		except:
			return (False, False)

	def activities_finish_video(self, weburl):
		r = post(f"{API_URL}/activity/finish_file", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		self.get_files("", True)
		self.get_categories(True)
		return str(r.decode("utf-8"))

	def activities_back_video(self, weburl):
		r = post(f"{API_URL}/activity/back_file", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		self.get_files("", True)
		self.get_categories(True)
		return str(r.decode("utf-8"))

	def activities_remove_video(self, weburl):
		r = post(f"{API_URL}/activity/remove_file", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		self.get_files("", True)
		self.get_categories(True)
		r = r.decode("utf-8")
		return str(r)

	def get_lastactivity(self):
		r = post(f"{API_URL}/activity/lastactivies", headers={"api-key":API_KEY})
		if not r:
			print("problem with post request. get_lastactivity")
			return ""
		#add apikey to first element of the list
		try:
			r_content:list = eval(r.content.decode("utf-8"))
			r_content.insert(0, API_KEY)
			return str(r_content)
		except:
			print(r.status_code, r.content)
			print_exc()
			return ""
	def flattenCategories(self, categories, parentPath = ''):
		flatCategories = []
		
		for key, value in categories.items():
			currentPath = parentPath + key + '/'
			flatCategories.append(currentPath)
			
			if isinstance(value, dict) and value:
				childCategories = self.flattenCategories(value, currentPath)
				if childCategories:
					flatCategories.extend(childCategories)
		
		return flatCategories

	def get_categories(self, remove_cache:bool=False):
		global CATEGORIES_LIST
		global CATEGORIES
		if remove_cache:
			CATEGORIES_LIST = []
			CATEGORIES = []
			print("get_categories cache cleared")
		if CATEGORIES_LIST == []:
			r = post(f"{API_URL}/upload/get_categories", headers={"api-key":API_KEY})
			CATEGORIES_LIST = r.json()
			# print(CATEGORIES_LIST)
			CATEGORIES = self.flattenCategories(CATEGORIES_LIST)
		return {'categories': CATEGORIES}
	
	def file_remove(self, weburl):
		weburl = int(weburl)
		r = post(f"{API_URL}/files/remove_file", headers={"api-key":API_KEY}, json={"weburl":weburl}).content
		if r == b"ok":
			return {'success': 1}
		else:
			return {'success': 0}
	
	def get_categories_list(self, catg:str=""):
		if catg.startswith("search:"):
			return False
		global CATEGORIES_LIST
		if catg == "":
			return {'categories': CATEGORIES_LIST}
		if catg[-1] == "/":
			catg = catg[:-1]
		catg_splitted = catg.split("/")

		result = CATEGORIES_LIST
		for part in catg_splitted:
			if not part:  # Skip empty parts
				continue

			if isinstance(result, dict) and part in result:
				result = result[part]
			else:
				return {'categories': [], "api_key": API_KEY}  # Path not found

		if isinstance(result, dict):
			return {'categories': list(result.keys()), "api_key": API_KEY}

		else:
			return {'categories': [], "api_key":API_KEY}
	def get_files(self, category:str="", remove_cache:bool=False):
		global FILES_LIST
		if remove_cache:
			FILES_LIST = []
			print("get_files cache cleared")
		if FILES_LIST == []:
			r:bytes = post(f"{API_URL}/files/getfiles", headers={"api-key":API_KEY}).content
			FILES_LIST = eval(r.decode("utf-8"))
		if category == "":
			return {'files': FILES_LIST}
		elif category == "*lastest":
			f = FILES_LIST
			f.sort(key=lambda x: x[7], reverse=True)
			f = [[i[0],i[1],i[2],i[5]] for i in f][:15]
			f.insert(0, API_KEY)
			return str(f)
		elif category.startswith("search:"):
			search_key = category[7:]
			print("searching", search_key)
			search_res = search_func(search_key)
			return {'files': search_res[0], "categories":search_res[1]}
		else:
			if category[-1] != "/":
				category = category + "/"
			_temp_ctg = []
			for i in FILES_LIST:
				if i[2] == category:
					_temp_ctg.append(i)
			_temp_ctg.sort(key=lambda x: x[0])
			return {'files': _temp_ctg, 'apikey': API_KEY}
	def searchinall(self, weburl:str):
		try:
			weburl_int = int(weburl)
		except:
			return {'file': None}
		global FILES_LIST
		if FILES_LIST == []:
			r = post(f"{API_URL}/files/getfiles", headers={"api-key":API_KEY}).content
			FILES_LIST = eval(r.decode("utf-8"))
		for i in FILES_LIST:
			if i[0] == weburl_int:
				return {'file': i}
		return {'file': None}

	def editvid(self, weburl, name, about, category, filetype, visibility):
		global ACCEPTED_CHR
		global CATEGORIES
		global API_KEY

		for chr in about:
			if chr not in ACCEPTED_CHR:
				return f"about_char: `{chr}` not accepted"
		if len(about) > 500:
			return "about is too long > 500"
		
		private = 1 if visibility == "private" else 0
		
		if category[-1] != "/":
			category = category + "/"
		if category not in CATEGORIES:
			return "category not accepted - not found"
		
		for chr in name:
			if chr not in ACCEPTED_CHR:
				return f"name_char: `{chr}` not accepted"
		len_name = len(name)
		if (len_name < 2) or (len_name > 256):
			return "name is too short or too long (2-256)"
		
		if not (filetype == "photo" or filetype == "video" or filetype=="text"):
			filetype = "other"
		try:
			weburl = int(weburl)
		except:
			return "weburl is not valid - must be int"
		try:
			r = post(f"{API_URL}/files/editfile", headers={"api-key":API_KEY}, json={"weburl":weburl,"name":name,"about":about,"category":category,"filetype":filetype,"private":private}).content
			if r == b"ok":
				self.get_files("", True)
				self.get_categories(True)
				return f"1success-{r.decode('utf-8')}"
			else:
				return f"failed to edit file - {r}"
		except Exception as e:
			return f"failed to edit file - {e}"
	
	def create_category(self, name:str, parent:str):
		global API_KEY
		for chr in name:
			if chr not in ACCEPTED_CHR:
				return f"name_char: `{chr}` not accepted"
		len_name = len(name)
		if (len_name < 2) or (len_name > 100):
			return "name is too short or too long (2-100)"
		try:
			r = post(f"{API_URL}/upload/create_category", headers={"api-key": API_KEY}, json={"name":name,"parent":parent}).content
			print(r)
			if r == b"ok":
				self.get_categories(True)
				return f"1success-{r.decode('utf-8')}"
			else:
				return f"failed to create category - {r}"
		except Exception as e:
			return f"failed to create category - {e}"
		

	def download_abort(self, weburl:str):
		global WINDOW
		changegui(True)
		isokay_toabort = WINDOW.create_confirmation_dialog("abort?", "do you want to abort?")
		if not isokay_toabort:
			changeconsole(f"aborting cancelled. continue with: {weburl}")
			changegui(False)
			return
		changeconsole(f"Aborting: {weburl}")
		try:
			download.abort()
			changeconsole(f"succesfully aborted: {weburl}")
			changegui(False)
			return abort({'status': 'success'})
		except Exception as e:
			print_exc()
			changeconsole(f"aborting error!: {weburl} e`{str(e)}`")
			changegui(False)
			return abort({'status': 'failed'})

	def download(self, weburl:str):
		global WINDOW
		# global CMD_DOWNLOAD
		# global PYTHON_VER
		changegui(True)
		changeconsole(f"downloading: {weburl}")
		weburl = ''.join(x for x in weburl if x.isdigit())
		outdir_dialog = WINDOW.create_file_dialog(FOLDER_DIALOG)
		if type(outdir_dialog) == list or type(outdir_dialog) == tuple or type(outdir_dialog) == set:
			outdir:str = outdir_dialog[0]
		else:
			changeconsole("selected folder is invalid. using default from config.")
			outdir = DEFAULT_OUTDIR
		try:
			result = download.run(weburl, outdir, print_callback=changeconsole)
			if result != True:
				changeconsole("!! something went wrong, download.")
				return abort({'status': result[1]})
		except Exception as e:
			changeconsole(f"Upload error: {str(e)}")
			return abort({'status': 'failed'})
		changeconsole(f"!!downloaded!! {weburl}")
		changeconsole("you can close the window now.")
		self.get_files("", True)
		self.get_categories(True)
		return abort({'status': 'success'})

	def upload_abort(self, f_name):
		global WINDOW
		changegui(True)
		isokay_toabort = WINDOW.create_confirmation_dialog("abort?", "do you want to abort?")
		if not isokay_toabort:
			changeconsole(f"aborting cancelled. continue with: {f_name}")
			changegui(False)
			return
		changeconsole(f"Aborting: {f_name}")
		try:
			upload.abort()
			changeconsole(f"succesfully aborted: {f_name}")
			changegui(False)
			return abort({'status': 'aborted succesfully'})
		except Exception as e:
			print_exc()
			changeconsole(f"aborting error!: {f_name} e`{str(e)}`")
			changegui(False)
			return abort({'status': 'failed'})

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
				fname:str = ffile.split("/")[-1]
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
				fname:str = items[1]
				ftype = items[4]
				if not (ftype == "photo" or ftype == "video" or ftype=="text"):
					ftype = "other"

			accp = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZıĞğÜüŞşİÖöÇç-,._()!+-[]{} ")
			for chr in fname:
				if chr not in accp:
					changeconsole(f"fail4 - {chr}")
					return abort({'status': 'fail'})
			len_fname = len(fname)
			if (len_fname < 2) or (len_fname > 256):
				changeconsole("fail5")
				return abort({'status': 'fail'})
			try:
				result = upload.run(str(ffile), str(fname), str(about), str(category), str(ftype), str(private), changeconsole)
				if result != True:
					changeconsole("!! something went wrong, uploading.")
					return abort({'status': result[1]})
			except Exception as e:
				changeconsole(f"Upload error: {str(e)}")
				return abort({'status': 'failed'})
			changeconsole(f"!!uploaded!! {fname}")
		changeconsole("you can close the window now.")
		self.get_files("", True)
		self.get_categories(True)
		return abort({'status': 'success'})
	
if __name__ == '__main__':
	try:
		api = Api()
		api.get_files()
		api.get_categories()
		# WINDOW = create_window('upload', fr"{CURRENT_PATH}/views/index.html?i=upload", js_api=api, width=width, height=height, resizable=False, text_select=True, background_color="#181818")
		WINDOW:Window = create_window('upload', fr"{CURRENT_PATH}/views/index.html?i=files", js_api=api, width=width, height=height, resizable=True, text_select=True, background_color="#181818")
	except:
		print_exc()
		WINDOW:Window = create_window('upload', fr"{CURRENT_PATH}/views/noapi.html", width=width, height=height, resizable=True, text_select=False, background_color="#181818")
	try:
		_arg1 = argv[1]
		start(http_port=PORT, gui="gtk", debug=(_arg1=="debug"), storage_path=fr"{CURRENT_PATH}/assets/.cache")
	except IndexError as e:
		print_exc()
		start(http_port=PORT, gui="gtk", debug=False, storage_path=fr"{CURRENT_PATH}/assets/.cache")
	except Exception as e:
		print_exc()
		print(e)
	