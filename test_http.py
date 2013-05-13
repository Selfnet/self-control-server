import SimpleHTTPServer
import SocketServer

import os
import posixpath
import BaseHTTPServer
import urllib
import cgi
import traceback
import sys
import shutil
import mimetypes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import sender

PORT = 8000

#Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

s = sender.Sender()


class myHTTPHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):

  def do_GET(self):
      self.do_POST()

  def do_POST(self):
    self.send_response(200)
    self.send_header("Content-type", 'text/plain')

    self.send_header("Content-Length", 0) #str(fs[6]))
    self.end_headers()
    try:
      (_,_,r,g,b) = self.path.split('/')
      print r,g,b
      s.setColorRGB(s.LEDALL,int(r),int(g),int(b) )
    except Exception,e:
      print 'err'
      traceback.print_exc(e)

Handler = myHTTPHandler

class Server(SocketServer.TCPServer):
    allow_reuse_address = True

httpd = Server(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()
