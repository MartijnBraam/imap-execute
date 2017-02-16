import imaplib


def start_idle(connection):
    tag = connection._new_tag().decode()
    connection.send("{} IDLE\r\n".format(tag).encode())
    response = connection.readline()
    connection.loop = True
    if response == b'+ idling\r\n':
        return
    else:
        raise Exception("IDLE not handled? : %s" % response)


def get_event(connection):
    resp = connection.readline().decode()
    print(resp)
    part = resp[2:].split('(', maxsplit=1)
    uid, message = part[0].strip().split(' ')
    return uid, message


def done(connection):
    connection.send("DONE\r\n".encode())
    while True:
        resp = connection.readline()
        if len(resp) > 0 and resp[0] != b'*':
            break


imaplib.IMAP4.start_idle = start_idle
imaplib.IMAP4.get_event = get_event
imaplib.IMAP4.done = done
