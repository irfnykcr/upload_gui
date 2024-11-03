import time
print(int(time.time()))


from subprocess import Popen
VLC = "C:/Program Files/VLC/vlc.exe"
# url = r"c:\Users\irfn\Desktop\diğer\PointlessMassiveDolphin.mp4"
url = "https://cdn.turkuazz.online/video?vid=664037273680"


proc = Popen(fr'"{VLC}" --intf qt --start-time=30 --extraintf http --http-port 8080 --http-password test123 {url}')

import requests
from requests.auth import HTTPBasicAuth
from time import sleep

# VLC HTTP API endpoint
vlc_url = 'http://localhost:8080/requests/status.json'
password = 'test123'  # Replace with your actual password

def get_info():
	try:
		duration = -1
		while duration == -1:
			response = requests.get(vlc_url, auth=HTTPBasicAuth('', password))
			response.raise_for_status()
			data = response.json()
			duration = data['length']
			sleep(0.5)
		return [duration]
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")
		return None

def get_current():
	try:
		response = requests.get(vlc_url, auth=HTTPBasicAuth('', password), timeout=1)
		response.raise_for_status()
		data = response.json()
		state = data['state']
		time = data['time']
		return [state,time]
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")
		return None
duration = get_info()[0]
currentstate = None
currenttime = None
while True:
	sleep(0.2)
	c = get_current()
	if c is None:
		print(f"{currenttime}/{duration}, ended")
		break
	if currentstate == c[0] and currenttime == c[1]:
		continue
	currenttime = c[1]
	currentstate = c[0]
	print(f"{currenttime}/{duration}, {currentstate}")