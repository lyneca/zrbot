import string
import requests
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from json import loads, dumps, load, dump
from urllib.parse import parse_qs

MANUAL_JSON_FILE = 'manual_australian_2018.json'

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', int(os.environ.get('PORT')))
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

bot_help = [
    '`/manual [topic]`: Look up a topic in the ZR manual.',
    '`/manual list`: List all the topic in the manual.',
    '`/manual help`: Display this help message.'
]

class Document:
    '''
    Abstract Base Class for documents. Do not instance.
    '''
    def __init__(self, f):
        self.filename = f
        self.file = {}
        self.to_dict()

    def to_dict(self):
        '''
        The only method you should need to implement for subclasses.
        Sets the `self.file` property to a dictionary mapping
        topics to lists of lines for that topic.
        '''
        pass

    def remove_punc(self, s):
        return ''.join([x for x in s if x not in string.punctuation])

    def find_page(self, query):
        for key in sorted(list(self.file.keys())):
            if query.lower() in key.lower():
                found_page = self.file[key]
                return (key, '\n'.join(found_page))
        return None

class JSONDocument(Document):
    def to_dict(self):
        with open(self.filename) as f:
            self.file = load(f)


class PythonDocument(Document):
    def to_dict(self):
        with open(self.filename) as f:
            # Totally secure
            self.file = eval(f)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if 'robots.txt' in self.path:
            self.send_response(200)
            self.end_headers()
        if '/oauth' not in self.path:
            return
        qs = parse_qs(self.path.split('?')[-1])
        print('team subscribed'.format(**qs))
        oauth_access = {
            'client_id': '224994577766.237977358084',
            'client_secret': os.environ.get('CLIENT_SECRET'),
            'code': qs['code'][0]
        }
        r = requests.post('https://slack.com/api/oauth.access', data=oauth_access)
        self.send_response(301)
        self.send_header('Location', 'https://lyneca.github.io/zrbot/thanks')
        self.end_headers()

    def do_POST(self):
        # Should just be POSTs from Slack with commands
        content_len = int(self.headers.get('content-length'))
        post_body = self.rfile.read(content_len).decode()
        post_body = parse_qs(post_body)
        for key in post_body:
            if type(post_body[key]) == list and len(post_body[key]) == 1:
                post_body[key] = post_body[key][0]
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        if 'text' not in post_body:
            self.end_headers()
            self.wfile.write('You need to send a request the same way that Slack does!')
        print("{team_domain}#{channel_name}@{user_id}: {command} {text}".format(**post_body))
        document = JSONDocument('data/' + MANUAL_JSON_FILE)
        found = document.find_page(post_body['text'])
        main_text = 'Search query not found.'
        attachment = ''

        if found:
            main_text = "Found a result in section %s:" % found[0]
            attachment = found[1]

        if post_body['text'][0].lower() == 'help':
            main_text = '\n'.join([
                "Use me to search the manual for you.",
                "If you get a timeout error when using me, try it again - I'm probably just booting up.",
                "Need help? Want to know how it works? Ask your mentor to contact Luke (or email me at lukemtuthill@gmail.com)",
                "Or visit https://lyneca.github.io/zrbot",
                "Here are the things I can do:"
            ])
            attachment = '\n'.join(bot_help)

        if post_body['text'][0].lower() == 'list':
            main_text = "Here are all the topics I can tell you about:"
            attachment = '\n'.join(sorted(list(document.file.keys())))

        response_dict = {
            'response_type': 'in_channel',
            'text': main_text,
            'attachments': [{
                'text': attachment,
                'mrkdwn_in': ['text']
            }]
        }
        self.end_headers()
        self.wfile.write(dumps(response_dict).encode('utf-8'))
        return

if __name__ == '__main__':
    run(HTTPServer, RequestHandler)
