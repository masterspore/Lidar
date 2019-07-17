import numpy as np
import scipy.io
import glob2
import time
import requests

from splinter import Browser

def filename_to_date(name):
	# start at 12
	return {"year" : name[12:14],
			"month" : name[14:16], 
			"day" : name[16:18]}

def filename_to_time(name):
	return name[18:20] + ":" + name[20:22]

def get_date_value(date):
	d = 'gdas1.'

	d += {
		'01': 'jan',
		'02': 'feb',
		'03': 'mar',
		'04': 'apr',
		'05': 'may',
		'06': 'jun',
		'07': 'jul',
		'08': 'aug',
		'09': 'sep',
		'10': 'oct',
		'11': 'nov',
		'12': 'dec',
	}.get(date["month"], 'jan')

	d += date["year"] + '.'

	day = int(date["day"])
	if 1 <= day <= 7:
		d += "w1"
	elif 8 <= day <= 14:
		d += "w2"
	elif 15 <= day <= 21:
		d += "w3"
	elif 22 <= day <= 28:
		d += "w4"
	elif 29 <= day <= 35:
		d += "w5"

	return d

def get_time_value(time):
	t = int(time[0:2])
	if int(time[3:5]) > 30:
		t += 1

	return str(t)

def choose_dropdown(b, name, value):
	dropdown = b.find_by_xpath("//select[@name='"+str(name)+"']")
	for option in dropdown.find_by_tag('option'):
		if option.text == value:
			option.click()
			break

def main():
	# Generate list from the files to analyse
	heights = []
	files = glob2.glob("Lidar_MPL/*.mat")
	for f in files:
		mat = scipy.io.loadmat(f)
		heights.append(
					{"date" : filename_to_date(f),
					"time" : filename_to_time(f),
					"Hmin" : mat["Hmin"][0][0],
					"Hmax" : mat["Hmax"][0][0],
					"filename" : f[10:22]}
					)

	for h in heights:
		print(h)

	# Open firefox to start uploading data to HySplit
	with Browser('firefox') as b:
		'''
		We go to the number of trajectories to calculate as the default is three, but 
		here the default option is one. We simply select 'next'
		'''
		b.visit("https://www.ready.noaa.gov/hypub-bin/trajtype.pl?runtype=archive")
		b.find_by_value('Next>>').click()

		# Now we need to repeat this process for each element in the list:
		resume = 42
		for h in heights[resume:len(heights)]:
			print(h)

			# Input location
			b.fill('Lat', '41.3840216')
			b.fill('Lon', '2.1093750')
			choose_dropdown(b, 'Lonew', 'E')
			b.find_by_value('Next>>').click()

			# We need to choose the adequate date
			d = get_date_value(h["date"])
			print(d)
			choose_dropdown(b, 'mfile', d)
			b.find_by_value('Next>>').click()

			# Finally we input the data required
			b.choose('direction', 'Backward')
			choose_dropdown(b, 'Start day', h["date"]["day"])
			choose_dropdown(b, 'Start hour', get_time_value(h["time"]))
			b.fill('duration', '48')
			b.fill('Source hgt1', str(h["Hmin"]))
			b.fill('Source hgt2', str(h["Hmax"]))
			b.find_by_value('Request trajectory (only press once!)').click()

			# Now the script needs to wait for the server to finish computing the trajectory
			time.sleep(60)

			# The files are ready, we will now store them
			link = b.find_link_by_partial_href('.gif')['href'][17:-3]
			print(link)
			with open('Lidar_MPL_gif/' + h["filename"] + '.gif', 'wb') as handle:
				response = requests.get("https://www.ready.noaa.gov" + link, stream=True)

				if not response.ok:
					print(response)

				for block in response.iter_content(1024):
					if not block:
						break
					handle.write(block)
        	
			print(h["filename"] + " done")

			# We start the process over again
			b.back()
			b.back()
			b.back()

if __name__ == '__main__':
	main()