from datetime import datetime
from json import load
from random import randint
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

r = post("https://api.turkuazz.online/v1/upload/get_categories", headers={"api-key":API_KEY})
try:
	allof = r.json()
except:
	print("error while getting categories. probably invalid api key.")
	exit()
CATEGORIES = []
for i in allof:
	CATEGORIES.append(f"{i}/")
	for k in allof[i]:
		CATEGORIES.append(f"{i}/{k}/")
		for l in allof[i][k]:
			CATEGORIES.append(f"{i}/{k}/{l}/")


width = 900
height = 720
settings = {
  'ALLOW_DOWNLOADS': False,
  'ALLOW_FILE_URLS': True,
  'OPEN_EXTERNAL_LINKS_IN_BROWSER': False,
  'OPEN_DEVTOOLS_IN_DEBUG': True
}


def changeconsole(msg):
	global WINDOW
	c = WINDOW.dom.get_element(".console")
	c.append(f"<p>{msg}</p>")
	WINDOW.evaluate_js('$(".console").scrollTop(999999);')
class Api:
	# def getRandomNumber(self):
	# 	response = {
	# 		'message': f"randint:{randint(1, 1000)}",
	# 	}
	# 	return response

	def echostuff(self,*msg):
		print(msg)
		return True
	
	def open_file_dialog(self):
		global WINDOW
		result = WINDOW.create_file_dialog(
			OPEN_DIALOG, allow_multiple=True, file_types=('All files (*.*)',)
		)
		return {'files': result,}
	
	def get_categories(self):
		global CATEGORIES
		global API_KEY
		return {'categories': CATEGORIES}
	
	def download(self, weburl:str):
		print("downloading..")
		changeconsole(f"downloading: {weburl}")
		global WINDOW
		global CMD_DOWNLOAD
		weburl = ''.join(x for x in weburl if x.isdigit())
		OUTDIR = WINDOW.create_file_dialog(FOLDER_DIALOG)
		if OUTDIR == None:
			changeconsole("selected folder is invalid. using default from config.")
			OUTDIR = DEFAULT_OUTDIR
		args = fr'"{weburl}" "{OUTDIR}"'
		changeconsole(f"{str(datetime.now()).split(' ')[1]}> {args}\n\n")
		proc = Popen(fr"{CMD_DOWNLOAD} {args}", stdout=PIPE, text=True, bufsize=1)
		while True:
			line = proc.stdout.readline()
			changeconsole(f"{str(datetime.now()).split(' ')[1]}> {line.strip()}\n\n")
			if not line:
				break
		changeconsole(f"{str(datetime.now()).split(' ')[1]}> you can close the window now.")
		return {'status': 'success'}
	
	def upload(self, items):
		global ACCEPTED_CHR
		global VIDEO_EXT
		global PHOTO_EXT
		global TXT_EXT
		global CATEGORIES
		global WINDOW
		changeconsole(f"items: {items}")
		FILE = items[0]

		about = items[2]
		accp = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!""#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ")
		for chr in about:
			if chr not in accp:
				changeconsole("fail1")
				return {'status': 'fai,l'}
		if len(about) > 500:
			changeconsole("fail2")
			return {'status': 'fail'}
		
		private = items[5]
		private = 1 if private == "private" else 0

		category = items[3]
		if category[-1] != "/":
			category = category + "/"
		if category not in CATEGORIES:
			changeconsole("fail3")
			return {'status': 'fail'}

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
					return {'status': 'fail'}
			len_fname = len(fname)
			if (len_fname < 2) or (len_fname > 100):
				changeconsole("fail5")
				return {'status': 'fail'}
			
			#generate thumbnail
			if (ftype == "video") or (ftype == "image"):
				random_name = fname + uuid4().hex[:5]
				args = fr'"{ffile}" "{random_name}" "{ftype}"'
				proc = Popen(fr"{CMD_GEN} {args}", stdout=PIPE, text=True, bufsize=1)
				changeconsole(args)
				while True:
					line = proc.stdout.readline()
					changeconsole(f"{line.strip()}")
					if not line:
						break
				changeconsole(f"generated random name. {random_name}")
			changeconsole("thumbnail generated. uploading file..")

			#uploading file		
			args = fr'"{ffile}" "{fname}" "{about}" "{category}" "{ftype}" "{private}"'
			proc = Popen(fr"{CMD_UPLOAD} {args}", stdout=PIPE, text=True, bufsize=1)
			changeconsole(args)
			while True:
				line = proc.stdout.readline()
				changeconsole(f"{line.strip()}")
				if not line:
					break
			changeconsole(f"!!uploaded!! {fname}")
		changeconsole("you can close the window now.")
		return {'status': 'success'}
	


if __name__ == '__main__':
	api = Api()
	WINDOW = create_window('xdxd_test', "views/index.html?i=upload", js_api=api, width=width, height=height, resizable=False, text_select=True, background_color="#181818")
	# window.confirm_close = True
	start(http_port=8000)