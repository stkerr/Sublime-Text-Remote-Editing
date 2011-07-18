import sublime,sublime_plugin

import subprocess
import os, time

# This plugin allows remote opening and saving of files


class RemoteCommand(sublime_plugin.TextCommand):

	configured = [False,False,False,False,True]

	username = ""
	password = ""
	host = ""
	filepath = ""
	port = "22"

	target = ""

	busy = False

	def isConfigured(self):
		if(self.configured[0] == False):
			return [False,0]
		elif(self.configured[1] == False):
			return [False,1]
		elif(self.configured[2] == False):
			return [False,2]
		elif(self.configured[3] == False):
			return [False,3]
		elif(self.configured[4] == False):
			return [False,4]
		else:
			return [True,-1]

	def getUsername(self,string):
		self.username = string
		self.configured[0] = True
		
	def getPassword(self,string):
		self.password = string
		self.configured[1] = True

	def getHost(self,string):
		self.host = string
		self.configured[2] = True

	def getFilepath(self,string):
		self.filepath = string
		self.configured[3] = True

	def getPort(self,string):
		self.port = string
		self.configured[4] = True

	def parsePreferences(self):
		
		# On Windows, this is how we reference the %APPDATA% variable
		path = os.environ['APPDATA'] + "\\Sublime Text 2\\Packages\\Remote\\config.txt"
		f = open(path , 'r')
		results = {}

		user = f.readline().split("\n")[0].split("=")[1]
		results.update({"username":user})
		self.configured[0] = True

		password = f.readline().split("\n")[0].split("=")[1]
		results.update({"password":password})
		self.configured[1] = True

		host = f.readline().split("\n")[0].split("=")[1]
		results.update({"host":host})
		self.configured[2] = True

		port = f.readline().split("\n")[0].split("=")[1]
		results.update({"port":port})
		self.configured[3] = True

		# Copy the values into the plugin now
		if(len(results) == 4):
			self.username = results['username']
			self.password = results['password']
			self.host 	  = results['host']
			self.port 	  = results['port']

	def savePaths(self,paths):
		print paths

		path = os.environ['APPDATA'] + "\\Sublime Text 2\\Packages\\Remote\\temp\path.txt"
		f = open(path , 'w')

		# Write out all the entries
		for e in paths.keys():
			line = e + ":" + paths[e] + "\n"
			print line
			f.write(line)

		f.close()

		return paths

	def parsePathfile(self):
		# Open up the path file
		path = os.environ['APPDATA'] + "\\Sublime Text 2\\Packages\\Remote\\temp\path.txt"
		f = open(path , 'r')

		# Read in all the entries
		lines = f.readlines()
		paths = {}
		for l in lines:
			l = l.split("\n")[0]
			print l
			print l.split(":")[0]
			print l.split(":",1)
			paths.update({l.split(":")[0]:l.split(":",1)[1]})
		f.close()

		return paths

	def openFilepath(self,file):
		# Generate the options string
		options = " -l " + self.username + " -pw " + self.password + " -P " + self.port + " "

		command = ""
		
		filename = file.split("/")[len(file.split("/"))-1]

		# Compute the target file
		target = "\"" + os.environ['APPDATA'] + "\\Sublime Text 2\\Packages\\Remote\\temp\\" + filename + "\""
		self.target = target

		# Generate the command string
		command = "pscp.exe " + options + " " + self.host + ":" + file + " " + target
		print command

		# Execute the string
		results = doSystemCommand(command)
		print results[0]
		print results[1]

		# Save the file mapping in the paths file
		existingpaths = self.parsePathfile()
		#print file
		#print target
		existingpaths.update({file:target})
		self.savePaths(existingpaths)


		sublime.status_message("Opening: " + target)

		# Since Sublime includes our current path in the open_file call,
		# we need to go back to the root before we open our file
		front = "..\\"
		for i in range(0,len(os.getcwd().split("\\"))):
			front = front + "..\\"

		sublime.Window.open_file(self.view.window(),front + os.environ['APPDATA'] + "\\Sublime Text 2\\Packages\\Remote\\temp\\" + filename)
		
		# path = os.environ['APPDATA'] + "\\Sublime Text 2\\Packages\\Remote\\temp\path.txt"
		# f = open(path , 'r+')
		# print file
		# print target
		# f.write(file + ":" + target + "\n")
		# f.close()


	def run(self, edit, mode, host, file):
		if(mode == "configure"):
			if(host == "username"):
				# Get the user's name
				self.view.window().show_input_panel("Username","",self.getUsername,None,None)
			elif(host == "password"):
				# Get the user's password
				self.view.window().show_input_panel("Password","",self.getPassword,None,None)
			elif(host == "host"):
				# Get the user's host
				self.view.window().show_input_panel("Host","",self.getHost,None,None)
			elif(host == "filepath"):
				# Get the user's file
				self.view.window().show_input_panel("Filepath","",self.getFilepath,None,None)
			elif(host == "port"):
				# Get the user's file
				self.view.window().show_input_panel("Port Number","",self.getPort,None,None)
			elif(host == "configure"):
				# Open and edit the user's preferences
				self.parsePreferences()

			return

		# Read the preferences file
		self.parsePreferences()

		configStatus = self.isConfigured()
		if(configStatus[0] == False):
			messages = ["Username", "Password", "Host", "Filepath", "Port"]
			sublime.status_message(messages[configStatus[1]] + " not configured!")
			return

		if(mode == "open"):

			# Get the file to open from the user
			self.view.window().show_input_panel("Filepath","",self.openFilepath,None,None)
			
		elif(mode == "save"):
			# Generate the options string
			options = " -l " + self.username + " -pw " + self.password + " -P " + self.port + " "

			# This is the buffer name that is open
			openfile =  sublime.active_window().active_view().file_name()

			# Change the buffer name formatting a little bit
			openfile = "\"" + openfile + "\""

			# Parse the pathfile
			paths = self.parsePathfile()

			found = False
			localpath = ""
			remotepath = ""
			for p in paths.keys():
				if(paths[p] == openfile):
					# We found the match, so assign the remote and local files to variables
					found = True
					localpath = paths[p]
					remotepath = p
					print paths[p] + " matches " + openfile
			
			if(found == False):
				# This file is not open in the paths file, so error out
				sublime.status_message("This file is not open for remote editing")
				return


			# Generate the command string
			command = "pscp.exe " + options + " " + localpath + " " + self.host + ":" + remotepath
			print command
	
			# Execute the command
			results = doSystemCommand(command)
			print results[0]
			print results[1]		
			
			# Let the user know we are done
			sublime.status_message("File saved!")	

		else:
			sublime.status_message("Invalid mode!")

# Runs a system command from the command line
# Captures and returns both stdout and stderr as a list, in that respective order
def doSystemCommand(commandText):
	p = subprocess.Popen(commandText, shell=True, bufsize=1024, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	p.wait()
	stdout = p.stdout
	stderr = p.stderr
	return [stdout.read(),stderr.read()]
	
# Displays given stderr if its not blank, otherwise displays stdout
# Method of display is configured using the Mode argument
#
# Results is of the form
# Results[0] is stdout to display
# Results[1] is stderr which, if its not None, will be displayed instead of stdout
#
# Modes:
# 	Window - Opens a new buffer with output
#	MessageBox - Creates a messageBox with output
#
# view is the view that will be used to create new buffers
def displayResults(Results, Mode, view):
	if(Mode == "Window"):
		if(Results[1] != None and Results[1] != ""):
			createWindowWithText(view, "An error or warning occurred:\n\n" + str(Results[1]))
		elif(Results[0] != None and Results[0] != ""):
			createWindowWithText(view, str(Results[0]))			
	# Message Box
	elif(Mode == "MessageBox"):
		if(Results[1] != None and Results != ""):
			sublime.status_message("An error or warning occurred:\n\n" + str(Results[1]))
		elif(Results[0] != None and Results[0] != ""):
			sublime.status_message(str(Results[0]))

# Open a new buffer containing the given text			
def createWindowWithText(view, textToDisplay):
	MercurialView = sublime.Window.newFile(view.window())
	MercurialView.insert(MercurialView.size(), textToDisplay)