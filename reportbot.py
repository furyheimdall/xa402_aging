# Parse logs from aging log

import sys
import time
import json
import telepot
import socket
import zipfile
import os
import datetime
import subprocess
import agingplot as ap

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
	global agingTitle
	global agingRunningOn
	global agingPath
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
			agingInfo = '* ' + line + '\n'
		elif 'Aging Name' in splitLine[0]:
			agingTitle = '* Current Aging Title :' + splitLine[1] + '\n'
		elif 'Running on' in splitLine[0]:
			agingRunningOn = '* Host : ' + splitLine[1] + '\n'
		elif 'Aging Path' in splitLine[0]:
			agingPath = '* Path : ' + splitLine[1] + '\n'
	elif len(splitLine) == 1:
		if 'memory monitoring on' in line:
			splitSubline = splitLine[0].split('monitoring on package ')
			agingInfo = agingInfo + '* Monitoring package : ' + splitSubline[1] + '\n'
			
		
def collectInfo(inputFile):
	global agingInfo
	global startTime
	global endTime
	global agingTitle
	global agingRunningOn
	global agingPath
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
	agingInfo = agingTitle + agingRunningOn + agingPath + agingInfo + '* Aging Period : ' + startTime + ' ~ ' + endTime + ' (elapsed : ' + str(elapsedDt) + ')'

def searchStringFromShell(command, save):
	fd_popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True).stdout
	log = fd_popen.read().strip()
	fd_popen.close()
	f = open(save, 'w')
	f.write(log)
	f.close()
	return len(log)

def handleTelegramChat(msg):
	content_type, chat_type, chat_id = telepot.glance(msg)
	
	if content_type == 'text':	
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
		elif '/getcrashhistory' in command :
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
		elif '/getcrashlog' in command :
			bot.sendMessage(chat_id, 'This command could take long time')
			cmd = ['egrep', '-n25', 'FATAL',  logDataPath]
			searchStringFromShell(cmd, './crashlog.txt')
			try:
				bot.sendDocument(chat_id, document=open('./crashlog.txt','rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'There are no crash logs currently')	
			os.remove('./crashlog.txt')
		elif '/getsuspicious' in command :
			bot.sendMessage(chat_id, 'This command could take long time')
			cmd = ['egrep', '-n', 'AudioFlinger could not create', logDataPath]
			szAudioFlinger = searchStringFromShell(cmd, './audioflinger.txt')
			cmd = ['egrep', '-n', 'no video decoders available', logDataPath]
			szNoVideoDec = searchStringFromShell(cmd, './novideodecoder.txt')
			try:
				if szAudioFlinger > 49 * 1024 * 1024:
					bot.sendMessage(chat_id, 'AudioFlinger suspicous log is too big')
				else :
					bot.sendDocument(chat_id, document=open('./audioflinger.txt','rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'There are no audio suspicious logs currently')
			try:
				if szNoVideoDec > 49 * 1024 * 1024:
					bot.sendMessage(chat_id, 'No video decoder suspicous log is too big')
				else :
					bot.sendDocument(chat_id, document=open('./novideodecoder.txt','rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'There are no video suspicious logs currently')
			os.remove('./audioflinger.txt')
			os.remove('./novideodecoder.txt')
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
			bot.sendMessage(chat_id, '[Supported CMDs]\n /aginginfo : to get aging information\n /getplotimg : to receive plot image\n /getplotdata : to receive plot data in txt\n /getlog : to receive log file\n /getcrashhistory : to receive crash history log\n /getcrashlog : to receive crash log in detail\n /getsuspicious : to receive suspicious log such that audio flinger could not create track')
	elif content_type == 'document':
		fileId = msg['document']['file_id']
		fileName = msg['document']['file_name']
		bot.download_file(fileId, './downloads/' + fileName)
		print ('Got file : ' + fileId + ' from ' + msg['chat']['first_name'] + '(' + str(chat_id) + ')')
		bot.sendMessage(chat_id, "Download complete")
		
def avoidPreviousMsgDuringShutdown():
	updates = bot.getUpdates()
	if updates:
	    last_update_id = updates[-1]['update_id']
	    bot.getUpdates(offset=last_update_id+1)
	
def entry(botToken, plotData, logData):
	global plotDataPath
	global logDataPath
	global bot
	if botToken == '':
		print("Please fill bot token here first in the reportbot.py")
		return
	os.makedirs('./downloads', exist_ok=True)
	plotDataPath = plotData
	logDataPath = logData	
	bot = telepot.Bot(botToken)
	avoidPreviousMsgDuringShutdown()
	bot.message_loop(handleTelegramChat)
	print('>>>>>>  Connected telegram bot : ' + bot.getMe()['first_name'])
	while True:
		time.sleep(10)

bot=''
plotDataPath='./mem.txt'
logDataPath=''
crashHistory=[]
timeCode=''
agingInfo=''
startTime=''
endTime=''
agingTitle=''
agingRunningOn=''
agingPath=''

if __name__ == '__main__':
	if len(sys.argv) >= 4:
		entry(sys.argv[1], sys.argv[2], sys.argv[3])
	elif len(sys.argv) >= 3:
		entry(sys.argv[1], sys.argv[2], '')
	else:
		print("Usage : python reportbot.py [botToken] [memfile] [logfile]")
		
'''
########################################
bot_token=''
########################################

entry(bot_token, 'example_memlog.txt','')
'''
