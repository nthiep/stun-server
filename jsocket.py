""" 
	@module jsocket
	Contains JsonSocket json object message passing for client.

	This file is part of the jsocket package.
"""

import base64, hashlib, random, string
import socket, struct, json, time, pickle
from config import SERVER_PORT
class JsonSocket(object):
	## defined variable
	TCP = 'TCP'
	UDP = 'UDP'
	def __init__(self, protocol):
		self.tcp 		= False
		if protocol == 'TCP':
			self.tcp 	= True
		if self.tcp:
			self.socket_obj = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		else:
			self.socket_obj= socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	def set_server(self, port=None):
		if port is None:
			self.port 	= SERVER_PORT
			self._bind(self.port)
		else:
			self.port = self._bind(port)
		if self.tcp:
			self._listen()
		return self.port

	def connect(self, address, port):
		if self.tcp:
			try:
				self.socket_obj.connect( (address, port) )
				logger.debug("socket: connected to server")
			except socket.error as msg:
				logger.debug("socket: %s" %msg)
				logger.debug("socket: can not connect to server")
				return False
		else:
			try:
				self.peer = (address, port)
				logger.debug("socket: UDP connected to server")
			except socket.error as msg:
				logger.debug("socket: %s" %msg)
				logger.debug("socket: UDP can not connect to server")
				return False
		return True

	def set_socket(self, sock):
		self.socket_obj= sock

	def gethostname(self):
		return socket.gethostname()
	def getpeername(self):
		return self.socket_obj.getpeername()	
	def get_conn(self):
		return self.socket_obj

	def send_obj(self, obj, peer=False):
		msg = json.dumps(obj)
		if self.socket_obj:
			if self.tcp:
				self.socket_obj.send(msg)
				return True
			elif peer:
				self.socket_obj.sendto(msg, peer)
				return True
		return False

	def read_obj(self):
		addr = None
		if self.tcp:
			msg = self._read(5120)
		else:
			msg, addr = self._read(5120)
		try:
			msg = json.loads(msg)
			if addr:
				return msg, addr
			return msg
		except:
			raise Exception('Request not Accept!')
	def _read(self, size):
		if self.tcp:
			data = self.socket_obj.recv(size)
			if data:
				return data
		else:
			data, addr = self.socket_obj.recvfrom(size)
			if data:
				return data, addr
		raise Exception('Socket Disconnect!')

	def _bind(self, port):
		self.socket_obj.bind( ("", port))
		return self.socket_obj.getsockname()[1]

	def _listen(self):
		self.socket_obj.listen(5)
	
	def _accept(self):
		return self.socket_obj.accept()
	def set_timeout(self):
		self.socket_obj.settimeout(self._timeout)

	def none_timeout(self):
		self.socket_obj.settimeout(None)

	def accept_connection(self):
		conn, addr = self._accept()
		conn.settimeout(self._timeout)
		return conn, addr

	def close(self):
		self.socket_obj.close()