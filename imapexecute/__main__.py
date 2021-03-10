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

    if raw[0] is None:
        return

    print('Executing action for account [{}]'.format(connection_name))
    mail = email.message_from_bytes(raw[0][1])

    environment = {
        'SUBJECT': mail.get('Subject'),
        'FROM': mail.get('From'),
        'DATE': mail.get('Date'),
        'TO': mail.get('To'),
        'CONNECTION': connection_name
    }

    mailfile = tempfile.mkstemp(prefix='imap-execute-')
    mailfile = open(mailfile[1], 'w+b')
    mailfile.write(mail.as_bytes(unixfrom=True))

    subprocess.Popen(config.get(connection_name, 'execute') + ' "' + mailfile.name + '"', shell=True, stdin=mailfile,
                     stdout=None, stderr=None,
                     close_fds=True, env=environment)


def loop():
    global connections
    global socket_list

    while True:
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [], 60)
        if len(read_sockets) == 0:
            # Timeout reached in select(), noop the connections to avoid tcp timeout
            for sock in socket_list:
                connection_name = sock.name
                connection = connections[connection_name]
                connection.done()
                connection.noop()
                connection.start_idle()

        for sock in read_sockets:
            connection_name = sock.name
            connection = connections[connection_name]
            uid, message = connection.get_event()
            if not uid:
                continue
            if message == 'EXISTS':
                connection.done()
                print('Fetching message {} for account [{}]'.format(uid, connection_name))
                status, datas = connection.fetch(uid, '(RFC822)')
                handle_message(connection_name, datas)
                connection.start_idle()
                print('Restarted idle')


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
