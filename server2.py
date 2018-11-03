import http.server
import mimetypes
import os
import posixpath
import shutil
import urllib.parse
import io

from http import HTTPStatus

class Handler(http.server.BaseHTTPRequestHandler):
	''' From SimpleHTTPRequestHandler, got common methods and 
		managed some of them
	'''
	def do_GET(self):
		f = self.send_head()
		if f:
			try:
				self.copyfile(f, self.wfile)
			finally:
				f.close()

	def send_head(self):
		path = self.translate_path(self.path)
		f = None
		if os.path.isdir(path):
			parts = urllib.parse.urlsplit(self.path)
			if not parts.path.endswith('/'):
				self.send_response(HTTPStatus.MOVED_PERMANENTLY)
				new_parts = (parts[0], parts[1], parts[2] + '/',
							 parts[3], parts[4])
				new_url = urllib.parse.urlunsplit(new_parts)
				self.send_header("Location", new_url)
				self.end_headers()
				return None

			index = os.path.join(path, "index.html")
			if os.path.exists(index):
				path = index
			else:									
				return self.list_directory(path)
		ctype = self.guess_type(path)
		try:
			f = open(path, 'rb')
		except OSError:
			self.send_error(HTTPStatus.NOT_FOUND, "File not found")
			return None
		try:
			self.send_response(HTTPStatus.OK)
			self.send_header("Content-type", ctype)
			fs = os.fstat(f.fileno())
			self.send_header("Content-Length", str(fs[6]))
			self.send_header("Last_Modified", self.date_time_string(fs.st_mtime))
			self.end_headers()
			return f
		except:
			f.close()
			raise

	def list_directory(self, path):

		try:
			list = os.listdir(path)
		except OSError:
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list list directory")
			return None
		list.sort(key=lambda a: a.lower())
		r = []
		try:
			displaypath = urllib.parse.unquote(self.path,
											   errors='surrogatepass')
		except UnicodeDecodeError:
			displaypath = urllib.parse.unquote(path)
		displaypath = html.escape(displaypath, quote=False)
		enc = sys.getfilesystemencoding()
		title = 'Directory listing for %s' % displaypath
		r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
				 '"http://www.w3.org/TR/htm14/strict.dtd">')
		r.append('<html>\n<head>')
		r.append('<meta http-equiv="Content-Type" '
				 'content="text/html; charset=%s' % enc)
		r.append('<title>%s</title>\n</head>' % title)
		r.append('<body>\n<h1>%s</h1>' % title)
		r.append('<hr>\n<ul>')
		for name in list:
			fullname = os.path.join(path, name)
			displayname = linkname = name
			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/"
			if os.path.islink(fullname):
				displayname = name + "@"
			r.append('<li><a href=%s>%s</a></li>'
					 % (urllib.parse.quote(linkname,
					 					   errors='surrogatepass'),
					 html.escape(displayname, quote=False)))
			r.append('</ul>\n<hr>\n</body>\n</html>\n')
			encoded = '\n'.join(r).encode(enc, 'surrogateescape')
			f = io.BytesIO()
			f.write(encoded)
			f.seek(0)
			self.send_response(HTTPStatus.OK)
			self.send_header("Content-type", "text/html; charset=%s" % enc)
			self.send_header("Content-Length", str(len(encoded)))
			self.end_headers()
			return f

	def translate_path(self, path):
		path = path.split('?',1)[0]
		path = path.split('#',1)[0]
		trailing_slash = path.rstrip().endswith('/')
		try:
			path = urllib.parse.unquote(path, errors='surrogatepass')
		except UnicodeDecodeError:
			path = urllib.parse.unquote(path)
		path = posixpath.normpath(path)
		words = path.split('/')
		words = filter(None, words)
		path = os.getcwd()
		for word in words:
			if os.path.dirname(word) or word in (os.curdir, os.pardir):
				continue
			path = os.path.join(path, word)
		if trailing_slash:
			path += '/'
		return path

	def copyfile(self, source, outputfile):
		shutil.copyfileobj(source, outputfile)

	def guess_type(self, path):
		base, ext = posixpath.splitext(path)
		if ext in self.extensions_map:
			return self.extensions_map[ext]
		ext = ext.lower()
		if ext in self.extensions_map:
			return self.extensions_map[ext]
		else:
			return self.extensions_map['']

	if not mimetypes.inited:
		mimetypes.init()
	extensions_map = mimetypes.types_map.copy()
	extensions_map.update({
		'': 'application/octet-stream',
		'.py': 'text/plain',
		'.c': 'text/plain',
		'.h': 'text/plain'
		})

HOST, PORT = '', 80

addr = (HOST, PORT)

listener = http.server.HTTPServer(addr, Handler)
print('http://%s:%s 주소에서 요청 대기중..' % (addr[0], addr[1]))
listener.serve_forever()