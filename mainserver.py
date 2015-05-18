#!/usr/bin/python
#
# Name:     Stun server
# Description:  NAT check.
# project 3
# Server:   amazon server
#
# Author:   Nguyen Thanh Hiep - Nguyen Huu Dinh
# Time:     2015/03
# Requirements:  requirements.txt
#

import sys, socket, json, random, hashlib, struct, thread
from threading import Thread
import logging.handlers, logging
from stun import StunServer
from jsocket import JsonSocket
from config import SERVER_PORT, OTHER_PORT, OTHER_SERVER, LOG_FILENAME
from config import OTHER_SERVER_REQUEST_TCP, OTHER_SERVER_REQUEST_UDP
global SECOND_TCP_SOCK
SECOND_TCP_SOCK=None
global SECOND_UDP_SOCK
SECOND_UDP_SOCK=None
class Server(Thread):
	TCP='TCP'
	UDP='UDP'
	def __init__(self, server_port, other_port, pro, second=False):
		super(Server, self).__init__()
		self.daemon 	= True
		self.tcp = False
		if pro=='TCP':
			self.tcp = True
			self.sock 	= JsonSocket(JsonSocket.TCP)
		else:
			self.sock 	= JsonSocket(JsonSocket.UDP)
		self.server_port = server_port
		self.other_port = other_port
		self.sock.set_server(server_port)
		if second:
			if self.tcp:
				global SECOND_TCP_SOCK
				SECOND_TCP_SOCK = self.sock
			else:
				global SECOND_UDP_SOCK
				SECOND_UDP_SOCK = self.sock 
	def process(self, obj, addr):
		if self.tcp:			
				conn 	= JsonSocket(JsonSocket.TCP)
				conn.set_socket(obj)
				conn.set_timeout()
				data	= conn.read_obj()
		else:
			data = obj
		print "%s request %s" %(str(addr), data)
		stun	= StunServer(self.server_port, self.other_port)
		response, request = stun.response(data, addr)
		print response, request
		if not response:
			return False
		if request == 2:			
			request_sock = JsonSocket(JsonSocket.TCP)
			if self.tcp:
				request_sock.connect(OTHER_SERVER, OTHER_SERVER_REQUEST_TCP)
			else:
				request_sock.connect(OTHER_SERVER, OTHER_SERVER_REQUEST_UDP)

			request_sock.send_obj(response)
			request_sock.close()
			return True
		elif request == 1:
			if self.tcp:
				SECOND_TCP_SOCK.send_obj(response)
			else:
				SECOND_UDP_SOCK.send_obj(response, addr)
			return True
		elif request == 0:
			if self.tcp:
				conn.send_obj(response)
				conn.close()
			else:
				print "send udp"
				self.sock.send_obj(response, addr)
			return True
		return False
	def run(self):
		print "server is running port %d..." %self.server_port
		if self.tcp:
			while True:
				connection, addr = self.sock.accept_connection()
				thread.start_new_thread(self.process, (connection, addr))
		else:
			while True:
				data, addr = self.sock.read_obj()
				thread.start_new_thread(self.process, (data, addr))

class SecondServer(Thread):
	""" second stun server """
	TCP = 'TCP'
	UDP = 'UDP'
	def __init__(self, server_port, pro):
		super(SecondServer, self).__init__()
		self.daemon 	= True
		self.tcp = False
		if pro == 'TCP':
			self.tcp=True
		self.server_port = server_port		
		self.sock 	= JsonSocket(JsonSocket.TCP)
		self.sock.set_server(server_port)
	def get_addr(self, data):
		""" get address of request """
		addr, port = data['XOR-MAPPED-ADDRESS'].split(":")
		return (addr, int(port))

	def process(self, connection, addr):
		conn 	= JsonSocket(JsonSocket.TCP)
		conn.set_socket(connection)
		conn.set_timeout()
		try:
			data	= conn.read_obj()
			print "%s request %s" %(str(addr), data)
			request_addr = self.get_addr(data)
			if self.tcp:
				send_sock 	= JsonSocket(JsonSocket.TCP)
				try:
					send_sock.connect(request_addr[0], request_addr[1])
					send_sock.send_obj(data)
					send_sock.close()
				except:
					print "cant not connect to %s:%d" %request_addr
			else:
				SECOND_UDP_SOCK.send_obj(data, request_addr)
			conn.close()
			return True
		except Exception, e:
			print e
			return False
	def run(self):
		print " second server is running port %d..." %self.server_port
		while True:
			connection, addr = self.sock.accept_connection()
			if addr[0] != OTHER_SERVER:
				connection.close()
				continue
			thread.start_new_thread(self.process, (connection, addr))

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
	def __init__(self, logger, level):
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level
 
	def write(self, message):
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "":
			self.logger.log(self.level, message.rstrip())

if __name__ == '__main__':
	"""
	logger = logging.getLogger(__name__)
	# Set the log level to LOG_LEVEL
	LOG_LEVEL = logging.INFO 
	logger.setLevel(LOG_LEVEL)
	# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
	handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
	# Format each log message like this
	formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
	# Attach the formatter to the handler
	handler.setFormatter(formatter)
	# Attach the handler to the logger
	logger.addHandler(handler)

		# Replace stdout with logging to file at INFO level
	sys.stdout = MyLogger(logger, logging.INFO)
	# Replace stderr with logging to file at ERROR level
	sys.stderr = MyLogger(logger, logging.ERROR)
	# run main script
	"""
	if len(sys.argv) == 2:
		if sys.argv[1] == 'second':
			second = SecondServer(OTHER_SERVER_REQUEST_UDP, SecondServer.UDP)
			second.start()

			second_tcp = SecondServer(OTHER_SERVER_REQUEST_TCP, SecondServer.TCP)
			second_tcp.start()
	second_server = Server(OTHER_PORT, SERVER_PORT, Server.UDP, second=True)
	second_server.start()
	primary_server = Server(SERVER_PORT, OTHER_PORT, Server.UDP)
	primary_server.start()
	
	second_server_tcp = Server(OTHER_PORT, SERVER_PORT, Server.TCP, second=True)
	second_server_tcp.start()
	primary_server_tcp = Server(SERVER_PORT, OTHER_PORT, Server.TCP)
	primary_server_tcp.start()
	primary_server_tcp.join()
