import os
import socket, threading  # NOQA: E401


exts_txt = ['.js', '.txt', '.css']
exts_bin = ['.html', '.jpg', '.gif', '.ico']

text_type_non_file_pages = ['/calculate-next', '/calculate-area', '/upload', '/image']
VALID_REQUEST_CODES = ['GET', "POST"]

moved_302 = {'A/dog.jpg': 'B/dog.jpg', 'B/dog.jpg': 'B/dog2.jpg'}

exit_all = False

PROTOCOL = 'HTTP1.1'

WEBROOT_LOCATION = 'd:/webroot'


def http_send(s, reply_header, reply_body, cli_num):
    reply = reply_header.encode()
    if reply_body != b'':
        try:
            body_length = len(reply_body)
            reply_header += 'Content-Length: ' + str(body_length) + '\r\n\r\n'
            if type(reply_body) != bytes:
                reply += reply_header.encode() + reply_body.encode()
            else:
                reply += reply_header.encode() + reply_body
        except Exception as e:
            print(e)
    else:
        reply += b'\r\n\r\n'
    s.send(reply)
    print(f'\n\nCli {cli_num} SENT: {reply_header}{reply_body[:min(200, len(reply))]}')


def http_recv(sock, cli_num, BLOCK_SIZE=8192):
    """
    :param sock: the client socket
    :param cli_num: number of the thread, for logging
    :param BLOCK_SIZE: the amount of bytes to do a 'receive' to

    :return:
    if got nothing or not according to protocol, returns b'',
    else returns
    """
    try:
        data = sock.recv(BLOCK_SIZE)
        # input(data)
        if data == b'':
            return b'', ''
        # data = data.decode()
        # print(data)
        end_of_headers = data.find(b'\r\n\r\n')
        if end_of_headers == -1:
            return b'', 'no'

        headers, body = data[:end_of_headers], data[end_of_headers + 4:]
        headers = headers.decode()

        print(f'\nCli {cli_num} - RECEIVED:', headers[:min(100, len(headers))])
        print(f'\nBody:{body[:min(100, len(body))]}')
        print(f'len: {len(body)}')

        headers = headers.split('\n')
        line1 = headers[0].split()

        if line1[0] not in VALID_REQUEST_CODES or line1[2] != 'HTTP/1.1':
            return b'', 'no'

        try:
            while True:
                new_body = sock.recv(BLOCK_SIZE)
                print(f'len: {len(new_body)}')
                body += new_body
        except socket.error:
            return headers[0], body
    except socket.error:
        return b'', 'timeout'


def get_type_header(requested_file):
    ret = ''

    if requested_file == '/':
        ret = 'Content-Type: text/html; charset=utf-8'

    elif requested_file in text_type_non_file_pages:
        ret = 'Content-Type: text/html; charset=utf-8'

    elif os.path.isfile(WEBROOT_LOCATION + requested_file):
        if '.' not in requested_file:
            ret = ''

        type_ = requested_file[requested_file.find('.'):]

        if type_ not in exts_bin or type_ not in exts_txt:
            ret = 'no'

        if type_ in ['.html', '.txt']:
            ret = 'Content-Type: text/html; charset=utf-8'
        elif type_ == '.jpg':
            ret = 'Content-Type: image/jpeg'
        elif type_ == '.js':
            ret = 'Content-Type: text/javascript; charset=UTF-8'
        elif type_ == '.css':
            ret = 'Content-Type: text/css'

    return ret + '\r\n'


def get_file_data(requested_file):
    with open(requested_file, 'rb') as f:
        cont = f.read()
    return cont


def get_next(x):
    x += 1
    return str(x)


def get_area(x, y):
    try:
        x, y = float(x), float(y)
        ret = x*y*0.5
        if ret % 1 == 0:
            ret = int(ret)

        return str(ret)
    except ValueError:
        return 'NaN'


def post_file(file_path, file_cont):
    try:
        with open(f'{file_path}', 'xb') as f:
            data_len = f.write(file_cont)

    except FileExistsError:
        i = 1
        file_path = file_path[:file_path.find('.png')] + f'({i}).png'
        while True:
            i += 1
            try:
                with open(f'{file_path}', 'xb') as f:
                    data_len = f.write(file_cont)
                break

            except FileExistsError:
                file_path = file_path.replace(f'({i - 1})', f'({i})')

    return str(data_len)  # the amount of data transferred to the file


def get_params(request):
    """
    :param request:
    :return: a list of values as: [val1, val2, ... ]
    """
    ret = request.split('&')
    ret = [i.split('=')[1] for i in ret]
    return ret


def handle_request(request_header, body):
    header = request_header.split()
    code = header[0]

    if code not in VALID_REQUEST_CODES:
        return 'HTTP/1.1 500 INVALID_REQUEST'


    the_whole_request = header[1].split('?')  # noqa: E303
    request = the_whole_request[0]
    params = ''
    if len(the_whole_request) > 1:
        params = the_whole_request[1]


    ret = ''  # noqa: E303
    type_ = get_type_header(request)
    if type_ == 'no':
        return 'HTTP/1.1 500 INVALID_REQUEST'

    header = 'HTTP/1.1 200 OK\r\n' + type_


    if code == 'GET':  # noqa: E303
        header, ret = if_get(request, params, header)
        # if request == '/':
        #     ret = get_file_data(f'{WEBROOT_LOCATION}/index.html')
        #
        # elif request == '/calculate-next':
        #     # num = params[1].split('=')[1]
        #     # num = int(num)
        #     num = int(get_params(params)[0])
        #     ret = get_next(num)
        #
        # elif request == '/calculate-area':
        #     # temp = get_params(params)
        #     # ret = get_area(temp[0], temp[1])
        #     height, width = get_params(params)
        #     ret = get_area(height, width)
        #
        # elif request == '/image':
        #     file_name = get_params(params)[0].replace('+', ' ').replace('%20', ' ')
        #     file = f'{WEBROOT_LOCATION}/imgs/{file_name}'
        #     if os.path.isfile(file):
        #         ret = get_file_data(file)
        #     else:
        #         header = 'HTTP/1.1 404 NOT_FOUND\r\n'
        #
        # else:
        #     request = WEBROOT_LOCATION + request  # .replace('/', '\\')
        #     if not os.path.isfile(request):
        #         header = 'HTTP/1.1 404 NOT_FOUND\r\n'
        #     else:
        #         ret = get_file_data(request)

    elif code == 'POST':
        header, ret = if_post(request, params, header, body)
        # if request == '/upload':
        #     if len(body) == 0:
        #         return 'HTTP/1.1 500 NO_IMAGE_TO_SAVE' #I don't know what would fit this so just generally 500 I guess
        #
        #     file_name = get_params(params)[0]
        #     file_name = file_name.replace('%20', ' ')
        #     directory = f'{WEBROOT_LOCATION}/imgs'
        #
        #     try:
        #         with open(f'{directory}/{file_name}', 'xb') as f:
        #             data_len = f.write(body)
        #     except FileExistsError:
        #         i = 1
        #         file_name = file_name[:file_name.find('.png')] + f'({i}).png'
        #         while True:
        #             i += 1
        #             try:
        #                 with open(f'{directory}/{file_name}', 'xb') as f:
        #                     data_len = f.write(body)
        #                 break
        #             except FileExistsError:
        #                 file_name = file_name.replace(f'({i-1})', f'({i})')
        #     ret = str(data_len)
        #     print(f'returning: {header}, {ret}')



    return header, ret  # noqa: E303
    

"""An option to make 'handle_request' more readable"""
"""
Pros: makes 'handle_request' shorter
      the way they they are organized without these is practically the same except as one long function
"""
"""
Cons: not sure how much it would help...
      if I want to change somthing it will have to fit 
"""


def if_get(request, params, header):
    ret = ''

    if request == '/':
        ret = get_file_data(f'{WEBROOT_LOCATION}/index.html')

    elif request == '/calculate-next':
        num = int(get_params(params)[0])
        ret = get_next(num)

    elif request == '/calculate-area':
        height, width = get_params(params)
        ret = get_area(height, width)

    elif request == '/image':
        file_name = get_params(params)[0].replace('+', ' ').replace('%20', ' ')
        file = f'{WEBROOT_LOCATION}/imgs/{file_name}'
        if os.path.isfile(file):
            ret = get_file_data(file)
        else:
            header = 'HTTP/1.1 404 NOT_FOUND\r\n'

    else:
        request = WEBROOT_LOCATION + request
        if not os.path.isfile(request):
            header = 'HTTP/1.1 404 NOT_FOUND\r\n'
        else:
            ret = get_file_data(request)

    return header, ret


def if_post(request, params, header, body):
    ret = ''

    if request == '/upload':
        if len(body) == 0:
            return 'HTTP/1.1 500 NO_IMAGE_TO_SAVE'  # I don't know what would fit this so just generally 500 I guess

        file_name = get_params(params)[0]
        file_name = file_name.replace('%20', ' ')
        directory = f'{WEBROOT_LOCATION}/imgs'

        # try:
        #     with open(f'{directory}/{file_name}', 'xb') as f:
        #         data_len = f.write(body)
        # except FileExistsError:
        #     i = 1
        #     file_name = file_name[:file_name.find('.png')] + f'({i}).png'
        #     while True:
        #         i += 1
        #         try:
        #             with open(f'{directory}/{file_name}', 'xb') as f:
        #                 data_len = f.write(body)
        #             break
        #         except FileExistsError:
        #             file_name = file_name.replace(f'({i - 1})', f'({i})')
        # ret = str(data_len)
        # # print(f'returning: {header}, {ret}')
        ret = post_file(f'{directory}/{file_name}', body)

    return header, ret


def handle_client(s_clint_sock, tid, addr):
    global exit_all
    print('\nnew client arrive', tid, addr)
    while not exit_all:
        request_header, body = http_recv(s_clint_sock, tid)
        if request_header == b'':
            if len(body) == 0:
                print('seems client disconnected ')  # , client socket will be close')
                break
            elif body == 'timeout':
                pass
            else:
                print("client sent an invalid request")
                break
        else:
            reply_header, body = handle_request(request_header, body)
            if PROTOCOL == "HTTP1.0":
                reply_header += "Connection': close\r\n"
            else:
                reply_header += "Connection: keep-alive\r\n"
            # print(f'Thread {tid} Going To Send: {reply_header}, {body}')
            http_send(s_clint_sock, reply_header, body, tid)
            if PROTOCOL == "HTTP1.0":
                break
    print("Client", tid, "Closing")
    s_clint_sock.close()


def main():
    global exit_all
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 80))
    server_socket.listen(5)
    threads = []
    tid = 1
    while True:
        try:
            # print('\n before accept')
            client_socket, addr = server_socket.accept()
            client_socket.settimeout(0.1)
            t = threading.Thread(target=handle_client, args=(client_socket, tid, addr))
            t.start()
            threads.append(t)
            tid += 1

        except socket.error as err:
            print('socket error', err)
            break

    exit_all = True
    for t in threads:
        t.join()

    server_socket.close()
    print('server will die now')


if __name__ == "__main__":
    main()
