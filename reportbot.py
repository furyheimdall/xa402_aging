# Parse logs from aging log

import sys
import time
import json
import telepot
import socket
import zipfile
import os
import datetime
import agingplot as ap

########################################
# Please fill bot token here first
bot_token=''
########################################

def maySplitFile(zipFile):
	files=[]
	memoryBuf=1024*1024*1024 # 1000MB
	partialSize=int(49*1024*1024) # 250MB
	zipSize=os.path.getsize(zipFile)
	if zipSize < partialSize: # if zip file size is less than partial size, send it directly
		files.append(zipFile)
		return files
	chapters = 1
	uglybuf = ''
	with open(zipFile, 'rb') as src:
		while True:
			tgt = open(zipFile + '.%03d' % chapters, 'wb')
			written = 0
			while written < partialSize:
				if len(uglybuf) > 0:
					tgt.write(uglybuf)
				tgt.write(src.read(min(memoryBuf, partialSize - written)))
				written += min(memoryBuf, partialSize - written)
				uglybuf = src.read(1)
				if len(uglybuf) == 0:
					break
			tgt.close()
			files.append(zipFile + '.%03d' % chapters)			
			if len(uglybuf) == 0:
				break
			chapters += 1
	os.remove(zipFile)	# remove original file	
	return files
			
def compress(file):
	zipTarget=file+'.zip'
	with zipfile.ZipFile(zipTarget, mode='w') as f:
		f.write(file, compress_type=zipfile.ZIP_DEFLATED)
	return zipTarget

def removeFiles(files):
	for targetFile in files:
		os.remove(targetFile)

def lineParse(line):
	global timeCode
	global agingInfo
	global startTime
	global endTime
	splitLine = line.split(':')
	if len(splitLine) > 1:
		if splitLine[0] == 'Current Time ':
			timeCode=splitLine[1]+':'+splitLine[2]+':'+splitLine[3]
			if startTime=='':
				startTime=timeCode
			else:
				endTime=timeCode
		elif 'PID of package' in splitLine[0]:
			crashHistory.append('[' + timeCode + '] ' + line)
		elif 'S/W fingerprint' in splitLine[0]:
			agingInfo = line + '\n'
	elif len(splitLine) == 1:
		if 'memory monitoring on' in line:
			splitSubline = splitLine[0].split('monitoring on package ')
			agingInfo = agingInfo + ' Monitoring package : ' + splitSubline[1] + '\n'
			
		
def collectInfo(inputFile):
	global agingInfo
	global startTime
	global endTime
	crashHistory.clear()
	agingInfo=''
	startTime=''
	endTime=''
	with open(inputFile,encoding='UTF-8') as f:
		fileContent = f.readlines()
		fileContent = [x.strip() for x in fileContent]
		for line in fileContent:
			lineParse(line)

	startTimeDt = datetime.datetime.strptime(startTime, ' %Y-%m-%d %H:%M:%S')
	endTimeDt = datetime.datetime.strptime(endTime, ' %Y-%m-%d %H:%M:%S')
	elapsedDt = endTimeDt-startTimeDt
	agingInfo = agingInfo + 'Aging Period : ' + startTime + ' ~ ' + endTime + ' (elapsed : ' + str(elapsedDt) + ')'

def handleTelegramChat(msg):
	chat_id = msg['chat']['id']
	command = msg['text']
	
	print ('Got command : ' + command + ' from ' + msg['chat']['first_name'] + '(' + str(chat_id) + ')')
	
	if '/chatid' in command :
		bot.sendMessage(chat_id, 'Current your chat ID is ' + str(chat_id))
	elif '/getplotimg' in command :
		bot.sendMessage(chat_id, 'Host name (' + socket.gethostname() + ') plotting from ' + plotDataPath)
		ap.generate_plot(plotDataPath)
		bot.sendPhoto(chat_id, photo=open('./graph.png','rb'))
		os.remove('./graph.png')
		ap.cleanup_plot()
	elif '/getplotdata' in command :
		bot.sendDocument(chat_id, document=open(plotDataPath, 'rb'))
	elif '/crashhistory' in command :
		collectInfo(plotDataPath)
		crashReporting=''
		for crash in crashHistory:
			crashReporting = crashReporting + '\n' + crash
		if len(crashReporting) >= 4096:
			f = open('./crashreporting.txt','w')
			f.write(crashReporting)
			f.close()
			bot.sendDocument(chat_id, document=open('./crashreporting.txt', 'rb'))
			os.remove('./crashreporting.txt')
		else:
			bot.sendMessage(chat_id, crashReporting)	
	elif '/getlog' in command :
		if logDataPath == '':
			bot.sendMessage(chat_id, 'Log file was not given')
		else :
			bot.sendMessage(chat_id, 'preparing logdata...')
			targetFiles=maySplitFile(compress(logDataPath))
			bot.sendMessage(chat_id, 'you will receive total ' + str(len(targetFiles)) + ' files === sending...')
			for sendFile in targetFiles:
				bot.sendDocument(chat_id, document=open(sendFile, 'rb'))
			bot.sendMessage(chat_id, 'send complete')
			removeFiles(targetFiles)
	elif '/aginginfo' in command:
		collectInfo(plotDataPath)
		global agingInfo
		bot.sendMessage(chat_id, agingInfo)
	else:
		bot.sendMessage(chat_id, 'Unknown command')
		bot.sendMessage(chat_id, '[Supported CMDs]\n /aginginfo : aging information\n /getplotimg : receive plot image\n /getplotdata : receive plot data in txt\n /getlog : receive log file\n /crashhistory : receive crash history log')

def avoidPreviousMsgDuringShutdown():
	updates = bot.getUpdates()
	if updates:
	    last_update_id = updates[-1]['update_id']
	    bot.getUpdates(offset=last_update_id+1)
	
def entry(plotData, logData):
	global plotDataPath
	global logDataPath
	plotDataPath = plotData
	logDataPath = logData
	avoidPreviousMsgDuringShutdown()
	bot.message_loop(handleTelegramChat)
	print('>>>>>>  Connected telegram bot : ' + bot.getMe()['first_name'])
	while True:
		time.sleep(10)

bot=telepot.Bot(bot_token)
plotDataPath='./mem.txt'
logDataPath=''
crashHistory=[]
timeCode=''
agingInfo=''
startTime=''
endTime=''


if __name__ == '__main__':
	if bot_token == '':
		print("Please fill bot token here first in the reportbot.py")
	elif len(sys.argv) >= 3:
		entry(sys.argv[1], sys.argv[2])
	elif len(sys.argv) >= 2:
		entry(sys.argv[1], '')
	else:
		print("Usage : python reportbot.py [memfile] [logfile]")
		
'''
entry('example_memlog.txt','')
'''
