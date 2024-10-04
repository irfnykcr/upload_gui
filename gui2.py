from datetime import datetime
from json import load
from subprocess import PIPE, Popen
from uuid import uuid4
from requests import post
from webview import OPEN_DIALOG, create_window, start, settings, FOLDER_DIALOG

with open("./config/config.json", "r") as f:
	j = load(f)
	CMD_UPLOAD = fr"{j['cmd_upload']}"
	CMD_DOWNLOAD = fr"{j['cmd_download']}"
	CMD_GEN = fr"{j['cmd_gen']}"
	API_KEY = j['api_key']
	DEFAULT_OUTDIR = j['outdir']
ACCEPTED_CHR = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZıĞğÜüŞşİÖöÇç-,._()!+-[]{} ")
VIDEO_EXT = [".mp4", ".mov", ".avi", ".wmv", ".mkv", ".webm", ".flv", ".ts"]
PHOTO_EXT = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
TXT_EXT = [".txt"]

CATEGORIES = []
CATEGORIES_LIST = []
FILES_LIST = []

width = 900
height = 807
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
	WINDOW.evaluate_js('$(".console").scrollTop(999999);')

def changegui(value:bool):
	global WINDOW
	elements = [".header-upload", ".header-download", ".header-logo"]
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

class Api:
	def echostuff(self,*msg):
		print(msg)
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
	
	def get_categories(self):
		global CATEGORIES
		if len(CATEGORIES) == 0:
			self.get_categories_list()
		return {'categories': CATEGORIES}
	def get_categories_list(self):
		global CATEGORIES_LIST
		global CATEGORIES
		if len(CATEGORIES_LIST) == 0:
			r = post("https://api.turkuazz.online/v1/upload/get_categories", headers={"api-key":API_KEY})
			CATEGORIES_LIST = r.json()
			CATEGORIES = []
			for i in CATEGORIES_LIST:
				CATEGORIES.append(f"{i}/")
				for k in CATEGORIES_LIST[i]:
					CATEGORIES.append(f"{i}/{k}/")
					for l in CATEGORIES_LIST[i][k]:
						CATEGORIES.append(f"{i}/{k}/{l}/")
		return {'categories': CATEGORIES_LIST}

	def get_files(self, category:str):
		global FILES_LIST
		if FILES_LIST == []:
			r:bytes = post("https://api.turkuazz.online/v1/files/getfiles", headers={"api-key":API_KEY}).content
			FILES_LIST = eval(r.decode("utf-8"))
		_temp_ctg = []
		for i in FILES_LIST:
			if i[2] == category:
				_temp_ctg.append(i)
		return {'files': _temp_ctg}

	def download(self, weburl:str):
		global WINDOW
		global CMD_DOWNLOAD
		changegui(True)
		changeconsole(f"downloading: {weburl}")
		weburl = ''.join(x for x in weburl if x.isdigit())
		OUTDIR = WINDOW.create_file_dialog(FOLDER_DIALOG)
		if OUTDIR == None:
			changeconsole("selected folder is invalid. using default from config.")
			OUTDIR = DEFAULT_OUTDIR
		args = fr'"{weburl}" "{OUTDIR}"'
		changeconsole(args)
		proc = Popen(fr"{CMD_DOWNLOAD} {args}", stdout=PIPE, text=True, bufsize=1)
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
				args = fr'"{ffile}" "{random_name}" "{ftype}"'
				proc = Popen(fr"{CMD_GEN} {args}", stdout=PIPE, text=True, bufsize=1)
				changeconsole(args)
				while True:
					line = proc.stdout.readline()
					changeconsole(line.strip())
					if not line:
						break
				changeconsole(f"generated random name. {random_name}")
			changeconsole("thumbnail generated. uploading file..")
	
			args = fr'"{ffile}" "{fname}" "{about}" "{category}" "{ftype}" "{private}"'
			proc = Popen(fr"{CMD_UPLOAD} {args}", stdout=PIPE, text=True, bufsize=1)
			changeconsole(args)
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
		api = Api()
		WINDOW = create_window('upload', "views/index.html?i=upload", js_api=api, width=width, height=height, resizable=False, text_select=True, background_color="#181818")
	except:
		WINDOW = create_window('upload', "views/noapi.html", width=width, height=height, resizable=False, text_select=False, background_color="#181818")
	start(http_port=8000)