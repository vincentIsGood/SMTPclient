# SMTP Client
This is a simple implementation of an SMTP.

The purpose of the project is to learn the basics of SMTP.

## Full example
The basics of SMTP is sending a bunch of commands.

```sh
# Connection Established
Server> 220 testmail.domain.com

Client> EHLO 1.2.3.4
Server> 250-testmail.domain.com Hello ....
Server> 250-option
Server> 250-option
Server> ...
Server> 250 HELP

Client> MAIL FROM: <your@email.com>
Server> 250 ... Sender ok

Client> RCPT TO: <receiver1@email.com>
Server> 250 ... Sender ok
Client> RCPT TO: <receiver2@email.com>
Server> 250 ... Recipient ok
Client> RCPT TO: <receiver3@email.com>
Server> 250 ... Recipient ok
Client> DATA
Server> 354 Enter mail, end with "." on a line by itself

Client> 
From: your@email.com
To: receiver1@email.com
Cc: receiver2@email.com, receiver3@email.com
Bcc: receiver2@email.com, receiver3@email.com
Subject: The first mail sent by hand
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary=randomseparatorstring

--randomseparatorstring
Content-Type: text/plain
Content-Transfer-Encoding: 7bit

Don't panic. I'm testing your understanding.

--randomseparatorstring
Content-Type: application/octet-stream
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename=test_your_understanding.png

iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAdSURBVChTY2RgYPgPxEQDJihNNBjVQAwY+hoYGABjsgEXlkNrGwAAAABJRU5ErkJggg==

--randomseparatorstring--
.

Server> 250 ... Message accepted for delivery
Client> QUIT
Server> 221 ... closing connection
# Connection closed
```