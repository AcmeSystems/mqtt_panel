#!/usr/bin/python
#
# mqtt_ledpanel.py
#
# Show a sliding text on RGB led panel
# 2014-2017 (c) Sergio Tanzilli - sergio@tanzilli.com - www.tanzolab.it
#
# Multiple panel capability added by Andrea Montefusco 2017, 
# Requires ledpanel.ko 2.0

import paho.mqtt.client as mqtt
import json
import time
import sys
import os
from datetime import datetime
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import StringIO
import probe

#Return the PIL color array from a web color (ie #55FF00)
def web2pil(webcolor):
	try:
		r=int(webcolor[1:3],16)*5/255
		g=int(webcolor[3:5],16)*5/255
		b=int(webcolor[5:7],16)*5/255
		return (r,g,b)
	except:
		return (1,1,1)

#Return the interface MAC address
def getmac(interface):
	try:
		mac = open('/sys/class/net/'+interface+'/address').readline()
	except:
		mac = "00:00:00:00:00:00"
	return mac[0:17]

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	global topic
	print("Connected with result code "+str(rc))
	client.subscribe(topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	global text,font,color,bgcolor,probe,x
	
	print("on_message: %s %s" % (msg.topic,msg.payload))
	try:
		j = json.loads(msg.payload)
		if j["cmd"]=="print":
			print j["font"]
			print j["color"]
			print j["bgcolor"]
			print j["text"]
			path = os.path.dirname(os.path.realpath(__file__))

			font=ImageFont.truetype("%s/fonts/%s" % (path,j["font"]), probe.panel_h)
			color=j["color"]
			bgcolor=j["bgcolor"]
			text=j["text"]
			x = probe.panel_w
			panel_clear(web2pil(j["bgcolor"]),probe.panel_w,probe.panel_h)

		if j["cmd"]=="clear":
			pass
	except:
			print "Message format error"

#Clear the led panel with bgcolor
def panel_clear(bgcolor,w,h):
	im = Image.new("RGB", (w,h), bgcolor)
	draw = ImageDraw.Draw(im)
	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	output = StringIO.StringIO()
	draw.rectangle((0,0,w,h),outline=bgcolor,fill=bgcolor)
	output.truncate(0)
	im.save(output, format='PPM')
	buf=output.getvalue()
	out_file.seek(0)
	out_file.write(buf[13:])

path = os.path.dirname(os.path.realpath(__file__))
print("Running from " + path)

print "Panel size: %d x %d\n" % (probe.panel_w, probe.panel_h)

broker="www.tanzolab.it"
port=1883
topic="acmesystems/mqtt_panel/%s/cmd" % (getmac("wlan0"))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, port, 60)

client.loop_start()
#client.loop_forever()

font = ImageFont.truetype(path + '/fonts/' 'Ubuntu-B.ttf', probe.panel_h)

text=getmac("wlan0")
color="#0000FF";
bgcolor="#000000";
loops=0
	
im = Image.new("RGB", (probe.panel_w, probe.panel_h), web2pil(bgcolor))
draw = ImageDraw.Draw(im)
draw.fontmode="1" #No antialias
  
out_file = open("/sys/class/ledpanel/rgb_buffer","w")
output = StringIO.StringIO()

x = probe.panel_w
while True:
	width, height = font.getsize(text)
	x=x-1
	
	if x < -(width):
		if loops==0:
			x = probe.panel_w
			continue
		else: 
			if loops==1:
				break
			else:
				loops=loops-1	
				x = probe.panel_w
				continue
		
	draw.rectangle((0, 0, probe.panel_w - 1, probe.panel_h), outline=web2pil(bgcolor), fill=web2pil(bgcolor))
	draw.text((x,-2), text, web2pil(color),font)

	output.truncate(0)
	im.save(output, format='PPM')
	buf=output.getvalue()

	out_file.seek(0)
	out_file.write(buf[13:])

out_file.close()
