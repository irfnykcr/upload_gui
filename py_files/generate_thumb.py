from json import load
from subprocess import check_output, run
from sys import argv
from threading import Thread
from os import path as os_path, makedirs
from cv2 import VideoCapture, imwrite, CAP_PROP_FRAME_COUNT, CAP_PROP_POS_FRAMES, IMWRITE_WEBP_QUALITY


FFMPEG = "ffmpeg -loglevel error"
EXTRA_WEBP = "-quality 1 -compression_level 6 -speed 6"
EXTRA_MP4 = "-crf 50 -b:v 50k -preset veryfast"
CV2_WEBP = 1

def getdur(url):
	return int(float(check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{url}'", shell=True).decode("utf-8").strip()))

def extract_middle_frame():
    global URL
    global OUTDIR
    cap = VideoCapture(URL)
    if not cap.isOpened():
        raise ValueError(f"Error: Cannot open video file {URL}.")
    frame_count = int(cap.get(CAP_PROP_FRAME_COUNT))
    middle_frame = frame_count // 2
    cap.set(CAP_PROP_POS_FRAMES, middle_frame)
    ret, frame = cap.read()
    if ret:
        output_path = f"{OUTDIR}/middle_frame.webp"
        imwrite(output_path, frame, [int(IMWRITE_WEBP_QUALITY), CV2_WEBP])
        print(f"Middle frame saved to {output_path}")
    else:
        raise ValueError("Error: Could not read the middle frame.")
    cap.release()

def generate():
	global OUTDIR
	global URL
	global DUR
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
	print("running cmd:", cmd)
	run(cmd, shell=True)
	# remove temp
	run(f"rm '{OUTDIR}/start.mp4' '{OUTDIR}/start_1.mp4' '{OUTDIR}/middle.mp4' '{OUTDIR}/middle_1.mp4' '{OUTDIR}/end.mp4'", shell=True)
	print("done")

def upfile():
	# server-side thingies
	return ""
if __name__ == "__main__":
	URL = fr"{argv[1]}"
	WEBURL = fr"{argv[2]}"
	FTYPE = fr"{argv[3]}"
	DUR = getdur(URL)
	randomname = str(abs(hash(URL)))
	with open(r"./config/config.json", "r") as f:
		j = load(f)
		OUTDIR = fr'{j["tmp_dir"]}/{randomname}'
		APIKEY = j["api_key"]
	if not os_path.exists(OUTDIR):
		makedirs(OUTDIR)
	print(f"url: {URL} && got dur: {DUR} && && outdir: {OUTDIR}")
	generate()
	extract_middle_frame()
	r = upfile()
	print("ok,", r)
	#remove tmp
	run(f"rm -r {OUTDIR}", shell=True)
print("\n\r")