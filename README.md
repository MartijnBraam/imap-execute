# IMAP Execute

This is a daemon that connects to one or multiple email boxes and uses IMAP IDLE to stream new messages.
For every new incoming message an user defined executable is run with the whole message and some metadata as input

## Config file

Create one ini section per mailbox:

```ini
[example box]
host=imap.gmail.com
port=993
username=my.email.address@gmail.com
password=secret
ssl=True

execute=/opt/test.sh
```

The `test.sh` script will be run for every incoming message with the following environment variables set:

| name | description             |
| ---  | ----                    |
| FROM | The source address      |
| TO   | The destination address |
| DATE | The date inside the envelope |
| SUBJECT | The e-mail subject line |
| CONNECTION | The ini section name of the mailbox that received the message |

The whole e-mail message in RFC822 format will be send to the standard input of the executable and as filename as first
argument.

Example executable:

```bash
#!/usr/bin/env bash

curl -X POST -F "from=$FROM" -F "to=$TO" -F "subject=$SUBJECT" -F "email=@$1;filename=email.eml" http://127.0.0.1:8000/email/upload
```