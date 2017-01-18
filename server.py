#  coding: utf-8 
import SocketServer
from urlparse import urlparse
import os

# Copyright 2013 Abram Hindle, Eddie Antonio Santos, David Yee
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

responses = {
    200 : "HTTP/1.1 200 OK\r\n",
    404 : "HTTP/1.1 404 Not Found\r\n",
    405 : "HTTP/1.1 405 Method Not Allowed\r\n"
}

content_type_header = "Content-Type: {0}; charset=utf-8\r\n\r\n"

root_uri = "./www/"

class MyWebServer(SocketServer.BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        request = self.data.split()
        http_verb = request[0] # GET, POST, PUT, etc.
        http_path = request[1] # Requested path (ie: /)
        http_version = request[2] # HTTP/1.1
        
        if http_verb == "GET":
            self.handle_get(http_path)
        else:
            self.request.sendall(responses[405])
    
    def handle_get(self, url):
        parsed_uri = urlparse(url)
        root_path_uri = root_uri + parsed_uri.path
        
        if os.path.isdir(root_path_uri):
            try:
                file = open(root_path_uri + "/index.html")
                response = responses[200] + content_type_header.format("text/html")
                
                # Output content of file into the response
                response += "".join(file.readlines())
                
                self.request.sendall(response)
            except IOError:
                self.request.sendall(responses[404])
        else:
            try:
                ext = os.path.splitext(root_path_uri)[1]
                file = open(root_path_uri)
                
                content_type = None
                if ext == ".css":
                    content_type = "text/css"
                else:
                    content_type = "text/html"

                response = responses[200] + content_type_header.format(content_type)
                
                # Output content of file into the response
                response += "".join(file.readlines())
                
                self.request.sendall(response)
            except IOError:
                self.request.sendall(responses[404])

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    SocketServer.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = SocketServer.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
