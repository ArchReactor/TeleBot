import tornado.ioloop
import tornado.web
import tornado.websocket
import serial
import thread

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)

class Arduino():
	
	def __init__(self, path='/dev/ttyUSB0', baud=115200):
		self.ser = serial.Serial(path, baud)	
	
	def send(self, data):
		self.ser.write(data)
		
	def read(self, bytes):
		while (1):
			if (self.ser.inWaiting() > bytes-1):
				return self.ser.read(bytes)
	
	def flush():
		self.ser.flushInput()
		self.ser.flushInput()
#end Arduino		

# store clients in dictionary..
clients = dict()

class IndexHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self):
		self.render("index.html", wsurl="ws://%s/ws" %(self.request.host))

class WebSocketHandler(tornado.websocket.WebSocketHandler):
	def open(self, *args):
		if len(clients.keys()) > 0:
			self.id = max(clients.keys()) + 1
		else:
			self.id = 1
		self.stream.set_nodelay(True)
		print "new Client %s connected" % (self.id)
		clients[self.id] = self
		self.write_message({ "type": "register", "clientid": self.id })

	def on_message(self, message):        
		print "Client %s sent a message : %s" % (self.id, message)
		m = tornado.escape.json_decode(message)
		m.update({"clientid": self.id})
		if m['type'] == "dir":
			bot.send("M" + m['data'])
		if m['type'] == "speed":
			bot.send("S" + m['data'])
		
		message = tornado.escape.json_encode(m)
		for client in clients:
			clients[client].write_message(message)
		
	def on_close(self):
		if clients[self.id]:
			print "Client %s disconnected" % (self.id)
			del clients[self.id]
#end WebSocketHandler

def MonitorBot():
	buf = ''
	while(1):
		b = bot.read(1)
		if b == "\n":
			print "Ardunio: %s" % (buf)
			cmd = buf.split(":")
			msg = {}
			if cmd[0] == 'P':
				msg['type'] = 'dir'
				msg['data']['dir'] = cmd[1]
				msg['data']['lt'] = cmd[2]
				msg['data']['rt'] = cmd[3]
				msg['data']['la'] = cmd[4]
				msg['data']['ra'] = cmd[5]
			
			if count(msg) > 0:
				message = tornado.escape.json_encode(msg)
				for client in clients:
					clients[client].write_message(message)
				
			buf = ''
		else:
			buf = buf + b
#end MonitorBot

app = tornado.web.Application([
	(r'/', IndexHandler),
	(r"/js/(.*)", tornado.web.StaticFileHandler, {"path": "js"}),
	(r'/ws', WebSocketHandler),
])

bot = Arduino('/dev/ttyUSB0', 115200)

if __name__ == '__main__':
	parse_command_line()
	thread.start_new_thread(MonitorBot)
	
	app.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
	print "Closing..."

