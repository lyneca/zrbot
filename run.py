import string
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from json import loads, dumps
from urllib.parse import parse_qs

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', int(os.environ.get('PORT')))
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

class Document:
    def __init__(self, filename):
        with open(filename) as f:
            self.file = eval(f.read())

    def remove_punc(self, s):
        return ''.join([x for x in s if x not in string.punctuation])

    def find_page(self, query):
        for key in self.file.keys():
            if query.lower() in key.lower():
                found_page = self.file[key]
                return (key, '\n'.join(found_page))
        return None

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print('Request from %s:%s' % self.client_address)
        content_len = int(self.headers.get('content-length'))
        post_body = self.rfile.read(content_len).decode()
        print(post_body)
        post_body = parse_qs(post_body)
        print(post_body)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        document = Document('manual.py')
        found = document.find_page(post_body['text'][0])
        main_text = 'Search query not found.'
        attachment = ''

        if found:
            main_text = "Found a result in section %s:" % found[0]
            attachment = found[1]

        response_dict = {
            'response_type': 'in_channel',
            'text': main_text,
            'attachments': [{
                'text': attachment
            }]
        }
        self.end_headers()
        self.wfile.write(dumps(response_dict).encode('utf-8'))
        return

if __name__ == '__main__':
    run(HTTPServer, RequestHandler)
