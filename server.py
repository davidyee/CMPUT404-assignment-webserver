#  coding: utf-8 
import SocketServer
import os
import posixpath
import mimetypes
import errno

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
    302 : "HTTP/1.1 302 Found\r\n",
    404 : "HTTP/1.1 404 Not Found\r\n",
    405 : "HTTP/1.1 405 Method Not Allowed\r\n",
    500 : "HTTP/1.1 500 Internal Server Error\r\n"
}

root_uri = "www/"
root_abs_path = os.path.abspath(os.path.join(root_uri, os.curdir))

class MyWebServer(SocketServer.BaseRequestHandler):
    http_host = None
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        if self.data:
            request_str = self.data.split()
            http_verb = request_str[0] # GET, POST, PUT, etc.
            http_path = request_str[1] # Requested path (ie: /)
            self.http_host = request_str[request_str.index("Host:") + 1]
            
            if http_verb == "GET":
                self.handle_get(http_path)
            else:
                self.request.sendall(responses[405])
    
    """
    Generate the response string to return to the client.
    
    Do not provide the "Content-Length" header as it will be determined 
    by this function.
    """
    def generate_response(self, status, file_abs_path=None):
        response_headers = ""
        content = ""
        length = 0
        
        if status >= 300 and status < 400:
            # Do not attempt to open any files for redirections
            response_headers += "Location: http://{0}\r\n".format(file_abs_path)
        elif file_abs_path is not None:
            try:
                ext = os.path.splitext(file_abs_path)[1]
                file = open(file_abs_path)
                
                content_type = mimetypes.guess_type(file.name)[0]
                if content_type is None:
                    content_type = "application/octet-stream"
        
                status = 200
                response_headers += "Content-Type: {0}; charset=utf-8\r\n".format(content_type)
                
                # Output content of file into the response
                content = "".join(file.readlines())
                length = len(content)
            except IOError, e: # Reset all
                if e.errno == errno.ENOENT: # File not found?
                    status = 404
                else: # Something catastrophic happened!
                    status = 500
                    
                response_headers = ""
                length = 0
                content = ""
        
        """ 
        Include the "Content-Length" header if applicable as defined by:
        https://www.w3.org/Protocols/HTTP/1.0/draft-ietf-http-spec.html#Entity-Body
        https://tools.ietf.org/html/rfc2616#section-14.13
        https://tools.ietf.org/html/rfc2616#section-4.4
        
        This header is not necessary for 1xx, 204, or 304 responses. 
        """
        if not((status >= 100 and status < 200) or status == 204 or status == 304):
            response_headers += "Content-Length: {0}\r\n".format(length)
        
        return responses[status] + response_headers + "\r\n" + content
    
    def handle_get(self, url):
        file_abs_path = os.path.normpath(
            os.path.abspath(root_abs_path + url)
        )
        
        response = ""
        if self.is_jailed(file_abs_path):
            if os.path.isdir(file_abs_path):
                if not (url.endswith("/") or url.endswith("\\")):
                    response = self.generate_response(302, posixpath.join(posixpath.normpath(self.http_host + url), ""))
                else:
                    response = self.generate_response(200, os.path.join(file_abs_path, "index.html"))
            elif os.path.isfile(file_abs_path):
                response = self.generate_response(200, file_abs_path)
            else:
                response = self.generate_response(404)
        else:
            response = self.generate_response(404)
        
        self.request.sendall(response)
    
    """
    Determines if the given file is permissible for retrieval. Only files that 
    are within the same directory or within some subdirectory of the webserver 
    root directory is allowed.
    
    Inspired by code written by  
    Jeff Terrace (http://stackoverflow.com/users/624900/jterrace) 
    on Stack Overflow (http://stackoverflow.com/a/6803714/2557554) and 
    licensed under CC BY-SA 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
    """ 
    def is_jailed(self, file_name):
        file_name = os.path.abspath(file_name)
        common_prefix = os.path.commonprefix([file_name, root_abs_path])
        return common_prefix == root_abs_path

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    SocketServer.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = SocketServer.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
