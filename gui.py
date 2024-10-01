from sys import stdout
from threading import Thread
from tkinter import Tk, Canvas, Entry, Text, Button, filedialog
from tkinter.ttk import Combobox
from json import load
from requests import post
from subprocess import PIPE, Popen
from datetime import datetime
from uuid import uuid4
stdout.reconfigure(line_buffering=True)

window = Tk()
width = 900
height = 720
x = (window.winfo_screenwidth() - width) // 2
y = (window.winfo_screenheight() - height) // 2
window.geometry(f"900x720+{x}+{y}")

window.title("upload")
window.iconbitmap(r"./assets/favicon.ico")
window.configure(bg = "#181818")

FILE = ""
ACCEPTED_CHR = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZıĞğÜüŞşİÖöÇç-,._()!+-[]{} ")
VIDEO_EXT = [".mp4", ".mov", ".avi", ".wmv", ".mkv", ".webm", ".flv", ".ts"]
PHOTO_EXT = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
TXT_EXT = [".txt"]
CANVAS1 = ""
CANVAS2 = ""
def page1():
	global t_fileloc
	global t_filename
	global t_about
	global t_category
	global t_type
	global t_private
	global b_start
	global t_console
	global gopage2
	global gopage1
	gopage2 = ""
	gopage1 = ""
	t_fileloc = ""
	t_filename = ""
	t_about = ""
	t_category = ""
	t_type = ""
	t_private = ""
	b_start = ""
	t_console = ""
	global CMD
	global CMD_GEN
	global CANVAS1
	global CANVAS2
	try:
		CANVAS2.destroy()
	except:
		pass
	CANVAS1 = Canvas(
		window,
		bg = "#181818",
		width = 900,
		height = 720,
		bd = 0,
		highlightthickness = 0,
		relief = "ridge"
	)
	CANVAS1.place(x = 0, y = 0)
	try:
		with open("./config/config.json", "r") as f:
			j = load(f)
			CMD = fr"{j['cmd_upload']}"
			CMD_GEN = fr"{j['cmd_gen']}"
			API_KEY = j['api_key']
		r = post("https://api.turkuazz.online/v1/upload/get_categories", headers={"api-key":API_KEY})
		CATEGORIES = r.json()
	except:
		# print("something went wrong. check your api key.")
		CANVAS1.create_text(
			150,
			300,
			anchor="nw",
			text="something went wrong. check your api key.",
			fill="#DADADA",
			font=("Inter", 32 * -1)
		)
		return
	
	def get_file():
		global FILE
		global ACCEPTED_CHR
		global VIDEO_EXT
		global PHOTO_EXT
		global TXT_EXT
		global t_type
		global t_fileloc
		global t_filename
		FILE = filedialog.askopenfilenames(title="Select file location", filetypes=(("All files", "*.*"),))
		if len(FILE) == 1:
			ffile = FILE[0]
			t_fileloc.config(text=ffile)
			t_filename.delete(0, "end")
			filename = ffile.split("/")[-1]
			ext = "." + filename.split(".")[-1]
			if ext in VIDEO_EXT:
				t_type.current(0)
			elif ext in PHOTO_EXT:
				t_type.current(1)
			elif ext in TXT_EXT:
				t_type.current(2)
			else:
				t_type.current(3)
			for i in filename:
				if i not in ACCEPTED_CHR:
					filename = filename.replace(i, "")
			t_filename.insert(0, filename)
			return 1
		else:
			t_fileloc.config(text=[i.split("/")[-1] for i in FILE])
			t_type.config(state="disabled", values=["auto"])
			t_type.current(0)
			t_filename.delete(0, "end")
			t_filename.insert(0, "auto")
			t_filename.config(state="disabled")
			return 1
	t_fileloc = Button(
		bg="#FFFFFF",
		fg="#000000",
		borderwidth=0,
		highlightthickness=0,
		command=get_file,
		relief="flat",
	)
	t_fileloc.place(
		x=416,
		y=26,
		width=350,
		height=24.0
	)

	t_filename = Entry(
		bd=0,
		bg="#FFFFFF",
		fg="#000000",
		highlightthickness=0
	)
	t_filename.insert(0, "filename")
	t_filename.place(
		x=416,
		y=82,
		width=350,
		height=24.0
	)

	t_about = Entry(
		bd=0,
		bg="#FFFFFF",
		fg="#000000",
		highlightthickness=0,
	)
	t_about.insert(0, "")
	t_about.place(
		x=416,
		y=138,
		width=350,
		height=24.0
	)

	allof = []
	for i in CATEGORIES:
		allof.append(f"{i}/")
		for k in CATEGORIES[i]:
			allof.append(f"{i}/{k}/")
			for l in CATEGORIES[i][k]:
				allof.append(f"{i}/{k}/{l}/")
	t_category = Combobox(
		window,
		values=allof,
		state="readonly",
	)
	t_category.place(
		x=416,
		y=193,
		width=350,
		height=24.0
	)
	t_category.current(0)

	choices = ["video","image","txt","other"]
	t_type = Combobox(
		window,
		values=choices,
		state="readonly",
	)
	t_type.place(
		x=416.0,
		y=250,
		width=350,
		height=24.0
	)
	t_type.current(0)

	choices = [0,1]
	t_private = Combobox(
		window,
		values=choices,
		state="readonly",
	)
	t_private.place(
		x=416,
		y=306,
		width=350,
		height=24.0
	)
	t_private.current(0)


	

	CANVAS1.create_text(
		241,
		300,
		anchor="nw",
		text="private",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	CANVAS1.create_text(
		259,
		244,
		anchor="nw",
		text="type",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	CANVAS1.create_text(
		228,
		188,
		anchor="nw",
		text="category",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	CANVAS1.create_text(
		249,
		132,
		anchor="nw",
		text="about",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	CANVAS1.create_text(
		224,
		76,
		anchor="nw",
		text="file name",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	CANVAS1.create_text(
		208,
		20,
		anchor="nw",
		text="file location",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	def upfunc():
		global t_fileloc
		global t_filename
		global t_about
		global t_category
		global t_type
		global t_private
		global b_start
		global FILE
		global CMD
		global gopage1
		global CMD_GEN
		global VIDEO_EXT
		global PHOTO_EXT
		global TXT_EXT
		gopage1.config(state="disabled")
		t_fileloc.config(state="disabled")
		t_filename.config(state="disabled")
		t_about.config(state="disabled")
		t_category.config(state="disabled")
		t_type.config(state="disabled")
		t_private.config(state="disabled")
		b_start.config(state="disabled")
		ftype = t_type.get()
		fname = t_filename.get()
		autocheck = (len(FILE) > 1)
		for ffile in FILE:
			change_console(f"now: {ffile}")
			if autocheck:
				fname = ffile.split("/")[-1]
				ext = "." + fname.split(".")[-1]
				if ext in VIDEO_EXT:
					ftype = "video"
				elif ext in PHOTO_EXT:
					ftype = "image"
				elif ext in TXT_EXT:
					ftype = "txt"
				else:
					ftype = "other"
			#generate thumbnail
			if (ftype == "video") or (ftype == "image"):
				random_name = fname + uuid4().hex[:5]
				args = fr'"{ffile}" "{random_name}" "{ftype}"'
				proc = Popen(fr"{CMD_GEN} {args}", stdout=PIPE, text=True, bufsize=1)
				change_console(args)
				while True:
					line = proc.stdout.readline()
					change_console(f"{line.strip()}")
					if not line:
						break
			change_console(f"generated random name. {random_name}")
			change_console("thumbnail generated. uploading file..")

			#uploading file		
			args = fr'"{ffile}" "{fname}" "{t_about.get()}" "{t_category.get()}" "{ftype}" "{t_private.get()}"'
			proc = Popen(fr"{CMD} {args}", stdout=PIPE, text=True, bufsize=1)
			change_console(args)
			while True:
				line = proc.stdout.readline()
				change_console(f"{line.strip()}")
				if not line:
					break
			change_console(f"!!uploaded!! {fname}")
		change_console("you can close the window now.")
		gopage1.config(state="normal")
		return

	def start():
		t = Thread(target=upfunc, daemon=False)
		t.start()
		
	b_start = Button(
		borderwidth=0,
		highlightthickness=0,
		command=start,
		relief="flat",
		text="start"
	)
	b_start.place(
		x=280,
		y=350,
		width=340,
		height=40
	)

	def change_console(txt):
		global t_console
		t_console.config(state="normal")
		txt = f"{str(str(datetime.now()).split(' ')[1])[:10]}> {txt}\n\n"
		t_console.insert("end", txt)

		t_console.config(state="disabled")
		t_console.see("end")
		return
	t_console = Text(
		bd=0,
		bg="#D9D9D9",
		fg="#000000",
		highlightthickness=0,
		state="disabled"
	)
	t_console.place(
		x=10,
		y=410,
		width=880,
		height=300
	)
	gopage1 = Button(
		borderwidth=0,
		highlightthickness=0,
		command=page2,
		relief="flat",
		text="go to download"
	)
	gopage1.place(
		x=25,
		y=150,
		width=150,
		height=50
	)


def page2():
	global t_fileloc
	global t_filename
	global t_about
	global t_category
	global t_type
	global t_private
	global b_start
	global t_console
	global gopage2
	global gopage1
	gopage2 = ""
	gopage1 = ""
	t_fileloc = ""
	t_filename = ""
	t_about = ""
	t_category = ""
	t_type = ""
	t_private = ""
	b_start = ""
	t_console = ""
	global CMD
	global CANVAS1
	global CANVAS2
	global OUTDIR
	try:
		CANVAS1.destroy()
	except:
		pass
	try:
		with open("./config/config.json", "r") as f:
			j = load(f)
			CMD = fr"{j['cmd_download']}"
	except:
		CANVAS1.create_text(
			150,
			300,
			anchor="nw",
			text="something went wrong. check your api key.",
			fill="#DADADA",
			font=("Inter", 32 * -1)
		)
		return
	CANVAS2 = Canvas(
		window,
		bg = "#181818",
		width = 900,
		height = 720,
		bd = 0,
		highlightthickness = 0,
		relief = "ridge"
	)
	CANVAS2.place(x = 0, y = 0)
	gopage2 = Button(
		borderwidth=0,
		highlightthickness=0,
		command=page1,
		relief="flat",
		text="go to upload"
	)
	gopage2.place(
		x=25,
		y=150,
		width=150,
		height=50
	)

	def select_outdir():
		global OUTDIR
		OUTDIR = filedialog.askdirectory()
		t_fileloc.config(text=OUTDIR)
	t_fileloc = Button(
		bg="#FFFFFF",
		fg="#000000",
		borderwidth=0,
		highlightthickness=0,
		command=select_outdir,
		relief="flat",
	)
	t_fileloc.place(
		x=416,
		y=26,
		width=350,
		height=24.0
	)

	t_filename = Entry(
		bd=0,
		bg="#FFFFFF",
		fg="#000000",
		highlightthickness=0
	)
	t_filename.place(
		x=416,
		y=82,
		width=350,
		height=24.0
	)

	CANVAS2.create_text(
		224,
		76,
		anchor="nw",
		text="file url",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	CANVAS2.create_text(
		208,
		20,
		anchor="nw",
		text="file location",
		fill="#DADADA",
		font=("Inter", 32 * -1)
	)

	def upfunc():
		global t_fileloc
		global t_filename
		global b_start
		global FILE
		global CMD
		global gopage2
		gopage2.config(state="disabled")
		t_fileloc.config(state="disabled")
		t_filename.config(state="disabled")
		b_start.config(state="disabled")
		fileurl = t_filename.get()
		fileurl = ''.join(x for x in fileurl if x.isdigit())
		args = fr'"{fileurl}" "{OUTDIR}"'
		change_console(f"{str(datetime.now()).split(' ')[1]}> {args}\n\n")
		proc = Popen(fr"{CMD} {args}", stdout=PIPE, text=True, bufsize=1)
		while True:
			line = proc.stdout.readline()
			change_console(f"{str(datetime.now()).split(' ')[1]}> {line.strip()}\n\n")
			if not line:
				break
		change_console(f"{str(datetime.now()).split(' ')[1]}> you can close the window now.")
		gopage2.config(state="normal")


	def start():
		t = Thread(target=upfunc, daemon=False)
		t.start()
		
	b_start = Button(
		borderwidth=0,
		highlightthickness=0,
		command=start,
		relief="flat",
		text="start"
	)
	b_start.place(
		x=280,
		y=150,
		width=340,
		height=40
	)


	def change_console(txt):
		global t_console
		t_console.config(state="normal")
		# t_console.delete("1.0", "end")
		t_console.insert("end", txt)
		t_console.config(state="disabled")
		t_console.see("end")

	t_console = Text(
		bd=0,
		bg="#D9D9D9",
		fg="#000000",
		highlightthickness=0,
		state="disabled"
	)
	t_console.place(
		x=10,
		y=210,
		width=880,
		height=500
	)

page1()
window.resizable(False, False)
window.mainloop()
