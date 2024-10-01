from json import load
from os.path import exists
from os import listdir, mkdir, remove, rename, system
from sys import argv, stdout
from cv2 import CAP_PROP_POS_FRAMES, imwrite, VideoCapture, CAP_PROP_FRAME_COUNT
thefile = fr"{argv[1]}"
r_name = argv[2]
ftype = argv[3]
with open(r"./config/config.json", "r") as f:
	j = load(f)
	OUT_DIR = j['outdir']
OUT = fr"{OUT_DIR}/{r_name}"
stdout.reconfigure(line_buffering=True)
def thevidframes(floc, amount:int):
	global OUT
	if not exists(OUT):
		mkdir(OUT)
	def getframes(frame, name):
		global video
		video.set(CAP_PROP_POS_FRAMES, frame)
		ret, frame = video.read()
		if not ret: return 0
		imwrite(fr'{OUT}\a{name}.webp', frame)
		return 1
	global video
	video = VideoCapture(floc)
	frames_amount = int(video.get(CAP_PROP_FRAME_COUNT))-1
	k = int(frames_amount/amount)
	theframes = [i*k-int(k/2) for i in range(1,amount+1)]
	print("using frames: ", theframes)
	n = 1
	for f in theframes:
		_n = (5-len(str(n)))
		if _n > 0:
			n = _n*"0" + str(n)
		getframes(f, n)
		n = int(n)
		n+=1
	print("frames done.")
def makewebp(name):
	global OUT
	system(fr'ffmpeg -v 32 -hide_banner -stats -loop 0 -framerate 1 -i "{OUT}\a%05d.webp" "{OUT}\{name}.webp"')
	print("video done!")

if ftype == "video":
	thevidframes(thefile, 6)
	makewebp("video")
	for f in listdir(OUT):
		if f == "a00003.webp":
			rename(fr"{OUT}\{f}", fr"{OUT}\still.webp")
		elif f[-4:] == ".webp":
			remove(fr"{OUT}\{f}")
else:
	thevidframes(thefile, 1)
	for f in listdir(OUT):
		if f == "a00001.webp":
			rename(fr"{OUT}\{f}", fr"{OUT}\still.webp")
		elif f[-4:] == ".webp":
			remove(fr"{OUT}\{f}")
