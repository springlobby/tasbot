#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, string, base64, hashlib, time, ParseConfig, thread, Plugin, traceback, Client, binascii, atexit
from customlog import *
from daemon import Daemon

class MainApp(Daemon,Plugin.ThreadContainer):
	"""main application object that has creates tasclient, pluginhandler and PingLoop instances"""
	def PingLoop(self):
		"""sned a PING to the server every 10 seconds until either dying is true or i got into an error state"""
		while not self.dying and self.er == 0:
			self.tasclient.ping()
			time.sleep(10)
		raise SystemExit(0)
	
	def onlogin(self,socket):
		"""start PingLoop and client mainloop, connect event handlers"""
		if self.firstconnect == 1:
			self.start_thread(self.tasclient.mainloop)
			self.start_thread(self.PingLoop)
			self.firstconnect = 0

		#self.tasclient.events.ondisconnected = self.ph.ondisconnected

		self.tasclient.events.onmotd = self.ph.onmotd
		self.tasclient.events.onsaid = self.ph.onsaid
		self.tasclient.events.onsaidex = self.ph.onsaidex
		self.tasclient.events.onsaidprivate = self.ph.onsaidprivate
		self.tasclient.events.onpong = self.ph.onpong
		self.tasclient.events.oncommandfromserver = self.ph.oncommandfromserver
		self.tasclient.events.ondisconnected = self.ph.ondisconnected

		self.ph.onloggedin(socket)
		self.ph.oncommandfromserver("ACCEPTED",[],self.tasclient.socket)
		self.connected = True
		Log.good("Logged in")

	def save_config(self):
		"""commit current config dictionary to file"""
		self.config.write(self.configfile)

	def is_admin(self,username):
		"""return true if either username or the asscoiated id is in self.admins"""
		if username in self.admins:
				return True
		elif username in self.tasclient.users:
				if "#"+str(self.tasclient.users[username].id) in self.admins:
						return True
				else:
						return False
		else:
				return False

	def do_login(self):
		"""handle tasserver login"""
		if self.tasclient.flags.register:
			Log.notice("Not logging in because a registration is in progress")
			return
		if self.verbose:
			Log.notice("Logging in...")
		m = hashlib.md5()
		m.update(self.config.get('tasbot',"password"))
		phash = base64.b64encode(binascii.a2b_hex(m.hexdigest()))
		self.tasclient.login(self.config.get('tasbot',"nick"),phash,"Newbot",2400,self.config.get('tasbot',"lanip","*"))

	def register(self,username,password):
		"""register new account on tasserver"""
		m = hashlib.md5()
		m.update(self.config.get('tasbot',"password"))
		self.tasclient.register(self.config.get('tasbot',"nick"),base64.b64encode(binascii.a2b_hex(m.hexdigest())))

	def destroy(self):
		"""deprecated"""
		self.tasclient.error = 1
		self.er = 1
		raise SystemExit(0)

	def reload_config(self):
		"""reload config and admins from file"""
		self.config = ParseConfig.Config(self.configfile)
		self.admins = self.config.GetOptionList('tasbot',"admins")

	def __init__(self,configfile,pidfile,register,verbose):
		"""default init and plugin loading"""
		super(MainApp, self).__init__(pidfile)
		self.firstconnect = 1
		self.er = 0
		self.connected = False
		self.cwd = os.getcwd()
		self.ph = Plugin.PluginHandler(self)
		self.configfile = configfile
		self.reload_config()
		self.config.set('tasbot','cfg_dir', self.cwd )
		self.verbose = verbose
		self.reg = register
		self.tasclient = Client.Tasclient(self)

		for p in self.config.GetOptionList('tasbot',"plugins"):
			self.ph.addplugin(p,self.tasclient)

		self.tasclient.events.onconnectedplugin = self.ph.onconnected
		self.tasclient.events.onconnected = self.do_login
		self.tasclient.events.onloggedin = self.onlogin
		self.dying = False
		

	def run(self):
		"""the main loop for MainApp, once this exists MainApp will be in unsable state"""
		if not self.daemonized:
			#we'll still drop a pidfile here to maek watchods happy
			pid = str(os.getpid())
			file(self.pidfile,'w+').write("%s\n" % pid)
			atexit.register(self.delpid) # Make sure pid file is removed if we quit
		while not self.dying:
			try:
				Log.notice("Connecting to %s:%i" % (self.config.get('tasbot',"serveraddr"),int(self.config.get('tasbot',"serverport"))))
				self.tasclient.connect(self.config.get('tasbot',"serveraddr"),int(self.config.get('tasbot',"serverport")))
				while not self.dying:
					time.sleep(10)
			except SystemExit:
				Log.info( "MainApp got SystemExit" )
				break
			except KeyboardInterrupt:
				Log.error("SIGINT, Exiting")
				self.ph.onexit()
				break
			except Exception, e:
				Log.error("parsing command line")
				Log.exception( e )
			time.sleep(10)
		self.ph.onexit()
		self.ph.unloadAll()
		self.ondestroy()
		self.tasclient.disconnect()
		self.tasclient = None
