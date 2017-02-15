import argparse
import configparser
from imapexecute.idle import imaplib
import email
import select
import subprocess
import tempfile

connections = {}
socket_list = []


def start_connection(name, config):
    global connections
    global socket_list

    if config['ssl']:
        connections[name] = imaplib.IMAP4_SSL(config['host'], port=int(config['port']))
    else:
        connections[name] = imaplib.IMAP4(config['host'], port=int(config['port']))

    connections[name].login(config['username'], config['password'])
    connections[name].select()
    connections[name].start_idle()
    socket = connections[name].socket()
    socket.name = name
    socket_list.append(socket)


def handle_message(connection_name, raw):
    global config

    print('New message for account [{}]'.format(connection_name))
    mail = email.message_from_bytes(raw[0][1])

    environment = {
        'SUBJECT': mail.get('Subject'),
        'FROM': mail.get('From'),
        'DATE': mail.get('Date'),
        'TO': mail.get('To'),
        'CONNECTION': connection_name
    }

    mailfile = tempfile.mkstemp(prefix='imap-execute-')
    mailfile.write(mail.as_bytes(unixfrom=True))

    subprocess.Popen(config.get(connection_name, 'execute'), shell=True, stdin=mailfile, stdout=None, stderr=None,
                     close_fds=True, env=environment)


def loop():
    global connections
    global socket_list

    while True:
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
        for sock in read_sockets:
            connection_name = sock.name
            connection = connections[connection_name]
            uid, message = connection.get_event()
            if message == 'EXISTS':
                connection.done()
                status, datas = connection.fetch(uid, '(RFC822)')
                handle_message(connection_name, datas)
                connection.start_idle()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="IMAP Executer")
    parser.add_argument('config', help='Config file location', type=open)

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read_file(args.config)

    print('Starting connections')
    for name in config.sections():
        if name != 'general':
            start_connection(name, config[name])

    print('Entering event loop')
    loop()
