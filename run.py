import string
import requests
import os
import time
import hmac
import hashlib

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
    """
    Abstract Base Class for documents. Do not instance.
    """
    def __init__(self, filename):
        self.filename = filename
        self.file = {}
        self.to_dict()

    def to_dict(self):
        """
        The only method you should need to implement for subclasses.
        Sets the `self.file` property to a dictionary mapping
        topics to lists of lines for that topic.
        """
        pass

    def remove_punc(self, s):
        return ''.join([x for x in s if x not in string.punctuation])

    def find_page(self, query):
        for key in sorted(list(self.file.keys()), key=lambda x: (len(x.split()[0]), x)):
            if query.lower() in key.lower():
                found_page = self.file[key]
                return (key, '\n'.join(found_page))
        return None

class JSONDocument(Document):
    """
    Reads a data file written in JSON.

    The format of the file should be as follows:
    ```
    {
        "1.1.1 Section Title I": [
            "Paragraph",
            "Paragraph",
            "Paragraph",
            "Paragraph",
            "Paragraph"
        ],
        "1.1.2 Section Title II": [
            "Paragraph",
            "Paragraph",
            "Paragraph",
            "Paragraph",
            "Paragraph"
        ]
    }
    ```
    """
    def to_dict(self):
        with open(self.filename) as f:
            self.file = load(f)


class PythonDocument(Document):
    """
    Reads a data file written in a Python Dict.

    Extremely vulnerable to pretty much any form of remote code execution.
    Do not use.
    """
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
            'client_id': '395118514789.394280839600',
            'client_secret': os.environ.get('CLIENT_SECRET'),
            'code': qs['code'][0]
        }
        requests.post('https://slack.com/api/oauth.access', data=oauth_access)
        self.send_response(301)
        self.send_header('Location', 'https://lyneca.github.io/zrbot/thanks')
        self.end_headers()

    def do_POST(self):
        # Should just be POSTs from Slack with commands
        content_len = int(self.headers.get('content-length'))
        post_body_raw = self.rfile.read(content_len)
        slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET').encode()
        timestamp = self.headers.get('X-Slack-Request-Timestamp')
        if abs(time.time() - float(timestamp)) > 60 * 5:
            return
        sig_basestring = 'v0:{}:{}'.format(timestamp, post_body_raw)
        my_signature = 'v0=' + hmac.new(
            slack_signing_secret,
            sig_basestring,
            hashlib.sha256
        ).hexdigest()
        slack_signature = self.headers.get('X-Slack-Signature').encode()
        if not hmac.compare_digest(my_signature, slack_signature):
            print("Signature mismatch")
            return

        post_body = parse_qs(post_body_raw.decode())
        for key in post_body:
            if type(post_body[key]) == list and len(post_body[key]) == 1:
                post_body[key] = post_body[key][0]
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        if 'text' not in post_body:
            self.end_headers()
            self.wfile.write(b'You need to send a request the same way that Slack does!')
        print("{team_domain}#{channel_name}@{user_id}: {command} \"{text}\"".format(**post_body))
        document = JSONDocument('data/' + MANUAL_JSON_FILE)
        found = document.find_page(post_body['text'])
        main_text = 'Search query not found.'
        attachment = ''

        if found:
            main_text = "Found a result in section %s:" % found[0]
            attachment = found[1]

        if post_body['text'].lower() == 'help':
            main_text = '\n'.join([
                "Use me to search the manual for you.",
                "If you get a timeout error when using me, try it again - I'm probably just booting up.",
                "Need help? Want to know how it works? Email lukemtuthill@gmail.com,",
                "or visit https://lyneca.github.io/zrbot.",
                "Manual version: *2018 Virtual Australian Comp* _(updated 11/5/2018)_",
                "Here are the things I can do:"
            ])
            attachment = '\n'.join(bot_help)
        elif post_body['text'].lower() == 'list':
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

if __name__ == '__main__':
    run(HTTPServer, RequestHandler)
