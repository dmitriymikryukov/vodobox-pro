import time,sys,os
sys.path.insert(0, '..')

os.environ['HOME']='/home/kiosk'
print("%a"%(os.environ,))

import pyautogui as p
import RPi.GPIO as GPIO

keyins=[6,13,19,26,12,16,20,21]

def kb_init_io():
	GPIO.setmode(GPIO.BCM)
	for k in keyins:
		GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def kb_key(n,pressed):
	if pressed:
		sz=p.size()
		bsw=sz[0]/8
		bsh=sz[1]/4
		y=bsh*(n%4)+(bsh/2)
		x=(bsw/2)
		if (n>=4):
			x=sz[0]-x
		print("gui-down: x=%s,y=%s"%(x,y))
		p.moveTo(x,y)
		p.mouseDown()	
	else:
		print("gui-up")
		p.mouseUp()	

def kb_thread():
	sz=p.size()
	print("Screen Size is: %s"%(sz,))
	ks=[False for i in range(len(keyins))]
	while True:
		i=0
		for n in keyins:
			prs=False if GPIO.input(n) else True
			if ks[i]!=prs:
				ks[i]=prs
				kb_key(i,prs)
			i+=1
		time.sleep(0.1)



kb_init_io()
kb_thread()

