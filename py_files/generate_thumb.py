from json import load
from subprocess import check_output, run
from threading import Thread
from os import path as os_path, makedirs, _exit
from cv2 import VideoCapture, imwrite, CAP_PROP_FRAME_COUNT, CAP_PROP_POS_FRAMES, IMWRITE_WEBP_QUALITY

#TODO: FIX SERVER SIDE UPLOADING

ABORT = 0

def abort():
	global ABORT
	ABORT = 1
	global PRINT_CALLBACK
	PRINT_CALLBACK("aborting..")
	exit()
	_exit()

def start(url, weburl, ftype, print_callback=print):
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	global FFMPEG
	global EXTRA_WEBP
	global EXTRA_MP4
	global CV2_WEBP
	FFMPEG = "ffmpeg -loglevel error"
	EXTRA_WEBP = "-quality 1 -compression_level 6 -speed 6"
	EXTRA_MP4 = "-crf 50 -b:v 50k -preset veryfast"
	CV2_WEBP = 1

	global URL
	global WEBURL
	global FTYPE
	global DUR
	global OUTDIR
	global APIKEY
	global PRINT_CALLBACK
	URL = fr"{url}"
	WEBURL = weburl
	FTYPE = ftype
	gd = getdur(URL)
	if isinstance(gd, tuple):
		return
	else:
		DUR = gd
	randomname = str(abs(hash(URL)))
	with open(r"./config/config.json", "r") as f:
		j = load(f)
		OUTDIR = fr'{j["tmp_dir"]}/{randomname}'
		APIKEY = j["api_key"]
	if not os_path.exists(OUTDIR):
		makedirs(OUTDIR)
	
	PRINT_CALLBACK = print_callback

	PRINT_CALLBACK(f"url: {URL} && got dur: {DUR} && && outdir: {OUTDIR}")
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	generate()
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	extract_middle_frame()
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	r = upfile()
	PRINT_CALLBACK(f"ok, {r}")
	#remove tmp
	run(f"rm -r {OUTDIR}", shell=True)
	return True



def getdur(url):
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	return int(float(check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{url}'", shell=True).decode("utf-8").strip()))

def extract_middle_frame():
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	global URL
	global OUTDIR
	global PRINT_CALLBACK
	cap = VideoCapture(URL)
	if not cap.isOpened():
		PRINT_CALLBACK(f"Error: Cannot open video file {URL}.")
		return False
	frame_count = int(cap.get(CAP_PROP_FRAME_COUNT))
	middle_frame = frame_count // 2
	cap.set(CAP_PROP_POS_FRAMES, middle_frame)
	ret, frame = cap.read()
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	if ret:
		output_path = f"{OUTDIR}/middle_frame.webp"
		imwrite(output_path, frame, [int(IMWRITE_WEBP_QUALITY), CV2_WEBP])
		PRINT_CALLBACK(f"Middle frame saved to {output_path}")
	else:
		PRINT_CALLBACK("Error: Could not read the middle frame.")
		return False
	cap.release()
	return True
def generate():
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	global OUTDIR
	global URL
	global DUR
	global PRINT_CALLBACK
	# segment and durations
	segment_duration = 3 if DUR > 15 else DUR / 5
	start = int(DUR*0.1)
	start_1 = int(DUR*0.25)
	middle = int(DUR*0.5)
	middle_1 = int(DUR*0.75)
	end = int(DUR*0.9)
	# adjust timestamps to ensure theyre within video bounds
	start = min(start, DUR - segment_duration)
	start_1 = min(start_1, DUR - segment_duration)
	middle = min(middle, DUR - segment_duration)
	middle_1 = min(middle_1, DUR - segment_duration)
	end = min(end, DUR - segment_duration)
	# run
	# Create threads for each segment
	threads = []
	commands = [
		(f"{FFMPEG} -ss {start} -i '{URL}' -t {segment_duration} -vf scale=320:320 {EXTRA_MP4} -filter:v fps=fps=6 -an '{OUTDIR}/start.mp4'", "start"),
		(f"{FFMPEG} -ss {start_1} -i '{URL}' -t {segment_duration} -vf scale=320:320 {EXTRA_MP4} -filter:v fps=fps=6 -an '{OUTDIR}/start_1.mp4'", "start_1"),
		(f"{FFMPEG} -ss {middle} -i '{URL}' -t {segment_duration} -vf scale=320:320 {EXTRA_MP4} -filter:v fps=fps=6 -an '{OUTDIR}/middle.mp4'", "middle"),
		(f"{FFMPEG} -ss {middle_1} -i '{URL}' -t {segment_duration} -vf scale=320:320 {EXTRA_MP4} -filter:v fps=fps=6 -an '{OUTDIR}/middle_1.mp4'", "middle_1"),
		(f"{FFMPEG} -ss {end} -i '{URL}' -t {segment_duration} -vf scale=320:320 {EXTRA_MP4} -filter:v fps=fps=6 -an '{OUTDIR}/end.mp4'", "end")
	]
	for cmd, name in commands:
		if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
		thread = Thread(target=lambda c: run(c, shell=True), args=(cmd,), name=name)
		threads.append(thread)
		thread.start()
	# Wait for all threads to complete
	for thread in threads:
		thread.join()
	# combine the files
	allmp4 = f"-i '{OUTDIR}/start.mp4' -i '{OUTDIR}/start_1.mp4' -i '{OUTDIR}/middle.mp4' -i '{OUTDIR}/middle_1.mp4' -i '{OUTDIR}/end.mp4'"
	partcount = allmp4.count(".mp4'")
	filter_complex = " ".join([f"[{i}:v]" for i in range(partcount)])
	cmd = f"{FFMPEG} {allmp4} -filter_complex '{filter_complex} concat=n={partcount}:v=1 [v]' -map '[v]' -vcodec libwebp {EXTRA_WEBP} -lossless 0 '{OUTDIR}/out.webp'"
	PRINT_CALLBACK(f"running cmd: {cmd}")
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	run(cmd, shell=True)
	# remove temp
	run(f"rm '{OUTDIR}/start.mp4' '{OUTDIR}/start_1.mp4' '{OUTDIR}/middle.mp4' '{OUTDIR}/middle_1.mp4' '{OUTDIR}/end.mp4'", shell=True)
	PRINT_CALLBACK("done")
	return  True

def upfile():
	global ABORT
	if ABORT: print("!!!abort signal!!!");return 0, "abort signal"
	#TODO: server-side thingies

	# return r
	return False