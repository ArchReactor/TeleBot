import tornado.ioloop
import tornado.web
import tornado.websocket

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)

# we gonna store clients in dictionary..
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
		message = tornado.escape.json_encode(m)
		for client in clients:
			clients[client].write_message(message)
		
	def on_close(self):
		if clients[self.id]:
			print "Client %s disconnected" % (self.id)
			del clients[self.id]
			

app = tornado.web.Application([
	(r'/', IndexHandler),
	(r"/js/(.*)", tornado.web.StaticFileHandler, {"path": "js"}),
	(r'/ws', WebSocketHandler),
])

if __name__ == '__main__':
	parse_command_line()
	app.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
	print "Closing..."
