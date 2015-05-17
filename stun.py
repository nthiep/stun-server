import struct, socket, time, logging
from config import SERVER_ADDR, SERVER_PORT, OTHER_PORT, OTHER_SERVER
#=============================================================================
#   STUN Server
# ============================================================================
class StunServer(object):
    def __init__(self, server_port, other_port):

        self.server_port = server_port
        self.other_port = other_port
    def ReadMessage(self, data):
        """ read message received"""
        try:
            StunType = data["STUN-TYPE"]
            ChangeRequest = data["CHANGE-REQUEST"]
            ChangeIP= data["CHANGE-IP"]
            ChangePort= data["CHANGE-PORT"]
            return (ChangeIP, ChangePort)
        except Exception, e:
            raise e
        return False
    
    def createResponse(self, address):
        """ send message"""
        data = {}
        data['MAPPED-ADDRESS']  = "%s:%d" %address
        data['RESPONSE-ORIGIN'] = "%s:%d" %(SERVER_ADDR, self.server_port)
        data['OTHER-ADDRESS']   = "%s:%d" %(OTHER_SERVER, self.other_port)
        data['XOR-MAPPED-ADDRESS']= "%s:%d" %address
        return data
    def createChangeResponse(self, address, ChangeIP=False, ChangePort=False):
        """ send message"""
        data = {}
        data['MAPPED-ADDRESS']  = "%s:%d" %address
        if ChangeIP and ChangePort:
            data['RESPONSE-ORIGIN'] = "%s:%d" %(OTHER_SERVER, OTHER_PORT)
        elif ChangePort:
            data['RESPONSE-ORIGIN'] = "%s:%d" %(SERVER_ADDR, self.other_port)
        else:
            data['RESPONSE-ORIGIN'] = "%s:%d" %(SERVER_ADDR, self.server_port)

        data['OTHER-ADDRESS']   = "%s:%d" %(OTHER_SERVER, OTHER_PORT)
        data['XOR-MAPPED-ADDRESS']= "%s:%d" %address
        return data

    def response(self, data, address):
        """ return response object """
        result = self.ReadMessage(data)
        if not result:
            data = {}
            data["BINDING-RESPONSE"] = False
            return (data, 0)
        ChangeIP, ChangePort = result
        if ChangeIP and ChangePort:
            """ call second server"""
            return (self.createChangeResponse(address, True, True), 2)
        elif ChangePort:
            """ respone in second port """
            return (self.createChangeResponse(address, False, True), 1)
        elif not ChangeIP and not ChangePort:
            return (self.createResponse(address), 0)
        else:            
            data = {}
            data["BINDING-RESPONSE"] = False
            return (data, 0)
