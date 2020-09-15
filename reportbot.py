# Parse logs from aging log

import sys
import time
import json
import telepot
import socket
import zipfile
import os
import datetime
import threading
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
	global targetIp
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
		elif 'Target device IP' in splitLine[0]:
			targetIp = splitLine[1].lstrip()	
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

	if startTime == '' or endTime == '' :
		return
	startTimeDt = datetime.datetime.strptime(startTime, ' %Y-%m-%d %H:%M:%S')
	endTimeDt = datetime.datetime.strptime(endTime, ' %Y-%m-%d %H:%M:%S')
	elapsedDt = endTimeDt-startTimeDt
	agingInfo = agingTitle + agingRunningOn + agingPath + agingInfo + '* Aging Period : ' + startTime + ' ~ ' + endTime + ' (elapsed : ' + str(elapsedDt) + ')'

def executeFromShellAndStore(command, save):
	fd_popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True).stdout
	log = fd_popen.read().strip()
	fd_popen.close()
	f = open(save, 'w')
	f.write(log)
	f.close()
	return len(log)

def executeFromShell(command) :
	fd_popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True).stdout
	log = fd_popen.read().strip()
	fd_popen.close()
	
def handleCrashHistory():
	collectInfo(plotDataPath)
	crashReporting=''
	for crash in crashHistory:
		crashReporting = crashReporting + '\n' + crash		
	return crashReporting       

def helpMssage():
	helpMsg='[Supported CMDs]\n'
	helpMsg+='/aginginfo : to get aging information\n'
	helpMsg+='/getplotimg : to receive plot image\n'
	helpMsg+='/getplotdata : to receive plot data in txt\n'
	helpMsg+='/getlog : to receive log file\n'
	helpMsg+='/getlog startline~endline : to receive partial log. ex) /getlog 1~100\n'
	helpMsg+='/getcrashhistory : to receive crash history log\n'
	helpMsg+='/getcrashlog : to receive crash log in detail\n'
	helpMsg+='/checktombstones : to receive tombstone history during this aging\n'
	helpMsg+='/gettombstone [tombstone_name] : to receive specific tombstone\n'
	helpMsg+='/getbugreport : to receive bugreport file\n'
	helpMsg+='/getsuspicious : to receive suspicious log such that audio flinger could not create track\n'
	helpMsg+='/register : to receive crash alarm\n'
	helpMsg+='/unregister : if you dont want to receive crash alarm\n'
	return helpMsg
		
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
			result = handleCrashHistory()
			if len(result) >= 4096:
				f = open('./crashreporting.txt','w')
				f.write(result)
				f.close()
				bot.sendDocument(chat_id, document=open('./crashreporting.txt', 'rb'))
				os.remove('./crashreporting.txt')
			else:
				bot.sendMessage(chat_id, result)	
		elif '/getcrashlog' in command :
			bot.sendMessage(chat_id, 'This command could take long time')
			cmd = ['egrep', '-n25', 'beginning of crash|FATAL',  logDataPath]
			executeFromShellAndStore(cmd, './crashlog.txt')
			try:
				bot.sendDocument(chat_id, document=open('./crashlog.txt','rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'There are no crash logs currently')	
			os.remove('./crashlog.txt')
		elif '/checktombstones' in command :
			bot.sendMessage(chat_id, 'This command could take long time')
			cmd = ['egrep', '-n', 'Tombstone written to:', logDataPath]
			executeFromShellAndStore(cmd, './tombstones.txt')
			try:
				bot.sendDocument(chat_id, document=open('./tombstones.txt','rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'There are no tombstones currently')
			os.remove('./tombstones.txt')
		elif '/gettombstone' in command :
			splitLine = command.split(' ')
			if len(splitLine) <= 1:
				bot.sendMessage(chat_id, "this command needs specific tombstone name. show help message")
				return
			tombstonePath = '/data/tombstones/' + splitLine[1]
			targetPath = './' + splitLine[1] + '.txt'
			if len(targetIp) < 9:
				cmd = ['adb', 'pull', tombstonePath, targetPath]
			else:
				cmd = ['adb', '-s', targetIp+':5555', 'pull', tombstonePath, targetPath]
			executeFromShell(cmd)
			try:
				bot.sendDocument(chat_id, document=open(targetPath, 'rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'There are no such tombstone data')
			except OSError as e:
				bot.sendMessage(chat_id, 'There are no such tombstone data')
			os.remove(targetPath)
		elif '/getbugreport' in command :
			bot.sendMessage(chat_id, 'Preparing bug report. This could take up to 5 min')
			if len(targetIp) < 9:
				cmd = ['adb', 'bugreport', '/tmp/bugreport.zip']
			else:
				cmd = ['adb', '-s', targetIp+':5555', 'bugreport', '/tmp/bugreport.zip']
			executeFromShell(cmd)
			try:
				bot.sendDocument(chat_id, document=open('/tmp/bugreport.zip', 'rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'Could not generate bugreport')
			except OSError as e:
				bot.sendMessage(chat_id, 'Could not generate bugreport')
		elif '/getsuspicious' in command :
			bot.sendMessage(chat_id, 'This command could take long time')
			cmd = ['egrep', '-n', 'AudioFlinger could not create|no video decoders available', logDataPath]
			szOutput = executeFromShellAndStore(cmd, './suspicious.txt')
			try:
				if szOutput > 49 * 1024 * 1024:
					bot.sendMessage(chat_id, 'suspicous log is too big')
				else :
					bot.sendDocument(chat_id, document=open('./suspicious.txt','rb'))
			except telepot.exception.TelegramError as terr:
				if 'non-empty' in terr.description:
					bot.sendMessage(chat_id, 'There are no suspicious logs currently')
			os.remove('./suspicious.txt')
		elif '/getlog' in command :
			if logDataPath == '':
				bot.sendMessage(chat_id, 'Log file was not given')
			else :
				splitLine = command.split(' ')
				if len(splitLine) <= 1:
					bot.sendMessage(chat_id, 'preparing full logdata...')
					targetFiles=maySplitFile(compress(logDataPath))
					bot.sendMessage(chat_id, 'you will receive total ' + str(len(targetFiles)) + ' files === sending...')
					for sendFile in targetFiles:
						bot.sendDocument(chat_id, document=open(sendFile, 'rb'))
					bot.sendMessage(chat_id, 'send complete')
					removeFiles(targetFiles)
				else:
					splitLine2 = splitLine[1].split('~')
					if len(splitLine2) <= 1:
						bot.sendMessage(chat_id, 'invalid parameter...')
					else:
						if int(splitLine2[0]) <= 0:
							bot.sendMessage(chat_id, 'start line must be >= 1')
						else:
							bot.sendMessage(chat_id, 'preparing partial logdata...')
							cmd = ['sed', '-n', splitLine2[0] + ',' + splitLine2[1] + 'p', logDataPath]
							print(cmd)
							szOutput = executeFromShellAndStore(cmd, logDataPath + '_filtered.txt')
							if szOutput <= 0:
								bot.sendMessage(chat_id, 'there are no result')
							else:
								targetFiles=maySplitFile(compress(logDataPath + '_filtered.txt'))
								bot.sendMessage(chat_id, 'you will receive total ' + str(len(targetFiles)) + ' files === sending...')
								for sendFile in targetFiles:
									bot.sendDocument(chat_id, document=open(sendFile, 'rb'))
								bot.sendMessage(chat_id, 'send complete')
								removeFiles(targetFiles)
		elif '/aginginfo' in command:
			collectInfo(plotDataPath)
			global agingInfo
			bot.sendMessage(chat_id, agingInfo)
		elif '/register' in command:
			listeners[chat_id] = msg['chat']['first_name']
			bot.sendMessage(chat_id, 'Registered')			
		elif '/unregister' in command:
			del listeners[chat_id]
			bot.sendMessage(chat_id, 'Unregistered')
		elif '/getlistener' in command:
			currentListeners=''
			for k in listeners.keys():
				currentListeners += (listeners[k] + ' ')
			if (len(currentListeners) == 0):
				bot.sendMessage(chat_id, "There are no listeners")
			else:
				bot.sendMessage(chat_id, currentListeners)
		else:
			bot.sendMessage(chat_id, 'Unknown command')
			bot.sendMessage(chat_id, helpMssage())
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

def notifyListeners(msg):
	for k in listeners.keys():
		bot.sendMessage(k, msg)
		
def monitorCrashHistory():
	global previousCrashHistory
	checkCrashHistory = handleCrashHistory()
	if len(checkCrashHistory) != len(previousCrashHistory):
		previousCrashHistory = checkCrashHistory
		notifyListeners("Crash detected on current aging")
	threading.Timer(10, monitorCrashHistory).start()
	
def monitorSuspicious():
	global previousSzSuspicious
	cmd = ['egrep', '-n', 'AudioFlinger could not create|no video decoders available', logDataPath]
	szOutput = executeFromShellAndStore(cmd, '/tmp/suspicious_monitor.txt_' + str(os.getpid()))
	print(str(previousSzSuspicious - szOutput))
	if szOutput - previousSzSuspicious > 1 * 1024 * 1024 :
		previousSzSuspicious = szOutput
		notifyListeners('Suspicious log are rapidly increasing... check ASAP : ' + str(int(previousSzSuspicious/1024)) + 'KB')
	os.remove('/tmp/suspicious_monitor.txt_' + str(os.getpid()))
	threading.Timer(600, monitorSuspicious).start()
	
def startBackgroundJob():
	monitorCrashHistory()
	monitorSuspicious()

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
	startBackgroundJob()
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
previousCrashHistory=''
previousSzSuspicious=0
targetIp=''
listeners=dict()

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
