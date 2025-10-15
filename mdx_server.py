# -*- coding: utf-8 -*-
# version: python 3.5

import threading
import re
import os
import json
import sys


if sys.version_info < (3, 0, 0):
    import Tkinter as tk
    import tkFileDialog as filedialog
else:
    import tkinter as tk
    import tkinter.filedialog as filedialog

from wsgiref.simple_server import make_server
from file_util import *
from mdx_util import *
from mdict_query import IndexBuilder

"""
browser URL:
http://localhost:8000/test
"""

URL_PREFIX = '/mydict'

content_type_map = {
    'html': 'text/html; charset=utf-8',
    'js': 'application/x-javascript',
    'ico': 'image/x-icon',
    'css': 'text/css',
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'mp3': 'audio/mpeg',
    'mp4': 'audio/mp4',
    'wav': 'audio/wav',
    'spx': 'audio/ogg',
    'ogg': 'audio/ogg',
    'eot': 'font/opentype',
    'svg': 'text/xml',
    'ttf': 'application/x-font-ttf',
    'woff': 'application/x-font-woff',
    'woff2': 'application/font-woff2',
}

# This gets the directory of the script or the executable, which is more reliable
base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        
resource_path = os.path.join(base_path, 'mdx')
print("resouce path : " + resource_path)
builder = None


def get_url_map():
    result = {}
    files = []

    # resource_path = '/mdx'
    file_util_get_files(resource_path, files)
    for p in files:
        if file_util_get_ext(p) in content_type_map:
            p = p.replace('\\', '/')
            result[re.match('.*?/mdx(/.*)', p).groups()[0]] = p
    return result


def application(environ, start_response):
    global builder
    path_info = environ['PATH_INFO'].encode('iso8859-1').decode('utf-8')

    if path_info == '/mydict/list_dicts':
        try:
            dict_files = [f for f in os.listdir(resource_path) if f.endswith('.mdx')]
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps(dict_files).encode('utf-8')]
        except Exception as e:
            start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
            return [json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8')]

    if path_info == '/mydict/set_dict':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
        request_body = environ['wsgi.input'].read(request_body_size)
        data = json.loads(request_body)
        dict_filename = data.get('path')
        if dict_filename:
            dict_path = os.path.join(resource_path, dict_filename)
            if os.path.exists(dict_path):
                builder = IndexBuilder(dict_path)
                start_response('200 OK', [('Content-Type', 'application/json')])
                return [json.dumps({'status': 'success', 'message': 'Dictionary loaded successfully.'}).encode('utf-8')]
        start_response('400 Bad Request', [('Content-Type', 'application/json')])
        return [json.dumps({'status': 'error', 'message': 'Invalid or missing dictionary path.'}).encode('utf-8')]

    # Handle URL_PREFIX
    if not path_info.startswith(URL_PREFIX):
        start_response('404 Not Found', [('Content-Type', 'text/plain; charset=utf-8')])
        return [b'Not Found. This server is configured with a URL prefix.']

    # Get the internal path by stripping the prefix
    path_info = path_info[len(URL_PREFIX):]
    if not path_info:
        path_info = '/'

    print('Internal path: %s' % path_info)
    m = re.match('/(.*)', path_info)
    word = ''
    if m is not None:
        word = m.groups()[0]

    url_map = get_url_map()

    if path_info in url_map:
        url_file = url_map[path_info]
        content_type = content_type_map.get(file_util_get_ext(url_file), 'text/html; charset=utf-8')
        start_response('200 OK', [('Content-Type', content_type)])
        return [file_util_read_byte(url_file)]
    elif builder is None:
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        injection_html_path = os.path.join(resource_path, 'injection.html')
        injection_content = file_util_read_byte(injection_html_path)
        message = b'<h1>No dictionary loaded. Please set one.</h1>'
        return [injection_content, message]
    elif file_util_get_ext(path_info) in content_type_map:
        content_type = content_type_map.get(file_util_get_ext(path_info), 'text/html; charset=utf-8')
        start_response('200 OK', [('Content-Type', content_type)])
        return get_definition_mdd(path_info, builder)
    else:
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return get_definition_mdx(path_info[1:], builder)


    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [b'<h1>WSGIServer ok!</h1>']


# 新线程执行的代码
def loop():
    # 创建一个服务器，IP地址为空，端口是8000，处理函数是application:
    httpd = make_server('', 8082, application)
    print("Serving HTTP on port 8082...")
    # 开始监听HTTP请求:
    httpd.serve_forever()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs='?', help="mdx file name")
    args = parser.parse_args()

    # use GUI to select file, default to extract
    # if not args.filename:
    #     root = tk.Tk()
    #     root.withdraw()
    #     args.filename = filedialog.askopenfilename(parent=root)

    if args.filename and not os.path.exists(args.filename):
        print("Please specify a valid MDX/MDD file")
    elif args.filename:
        builder = IndexBuilder(args.filename)

    t = threading.Thread(target=loop, args=())
    t.start()

