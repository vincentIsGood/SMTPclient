#!/usr/bin/python3

# Development platform: Windows 10
# Python version: 3.11.2

from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import messagebox
from tkinter import filedialog
import re
from io import BufferedReader
import os
import pathlib
import sys
import base64
import socket

#
# Global variables
#

YOUREMAIL = "bob@sendhelp.org"
MARKER = 'randomseparatorstring'

# The Email SMTP Server
SERVER = "testmail.domain.com"  # SMTP Email Server
SPORT = 25  # SMTP listening port

# For storing the attachment file information
fileobj = None  # For pointing to the opened file
filename = ''  # For keeping the filename

############################
##     Start of SMTP      ##
############################

#
# For the SMTP communication
#

###
## Main Function: "send" button handler
###
def do_Send():
    toEmails = parseEmailList(get_TO(), "TO", retNoneIfError=True, required=True)
    ccEmails = parseEmailList(get_CC(), "CC", retNoneIfError=True)
    bccEmails = parseEmailList(get_BCC(), "BCC", retNoneIfError=True)

    if toEmails == None or ccEmails == None or bccEmails == None:
        return

    if len(toEmails) == 0:
        alertbox("Must enter the recipient's email")
        return

    if get_Subject().strip() == "":
        alertbox("Must enter email subject")
        return

    if get_Msg().strip() == "":
        alertbox("Must enter email message")
        return

    try:
        with connectToServer() as sock:
            # wait for server response
            exchangeMsg(sock, None, receiveOnly=True, expectFirst="220")
            greetServer(sock)
            sendEmail(sock, toEmails, ccEmails, bccEmails)
            exchangeMsg(sock, wrapCRLF("QUIT"), expectFirst="221")
        alertbox("Successful")
    except ValueError as e:
        # debugLog(str(e))
        alertbox(str(e))



def connectToServer():
    sock = socket.socket(socket.AF_INET)
    sock.connect((SERVER, SPORT))
    sock.settimeout(60)  # 60s
    return sock


def greetServer(sock: socket.socket):
    exchangeMsg(sock, wrapCRLF("EHLO localhost"), readUntilContains="250 HELP", expectFirst="250")
    # exchangeMsg(sock, wrapCRCL("HELO localhost"))
    # exchangeMsg(sock, wrapCRCL("AUTH LOGIN"))
    # exchangeMsg(sock, wrapCRCL("user"))
    # exchangeMsg(sock, wrapCRCL("pass"))


def sendEmail(sock: socket.socket, toEmails: list[str], ccEmails: list[str], bccEmails: list[str]):
    global fileobj
    global filename

    exchangeMsg(sock, wrapCRLF("MAIL FROM: <%s>" % YOUREMAIL), expectFirst="250")
    for email in toEmails:
        exchangeMsg(sock, wrapCRLF("RCPT TO: <%s>" % email), expectFirst="250")
    for email in ccEmails:
        exchangeMsg(sock, wrapCRLF("RCPT TO: <%s>" % email), expectFirst="250")
    for email in bccEmails:
        exchangeMsg(sock, wrapCRLF("RCPT TO: <%s>" % email), expectFirst="250")
    exchangeMsg(sock, wrapCRLF("DATA"), expectFirst="354")

    dataStr = wrapCRLF("From: %s" % YOUREMAIL)
    dataStr += wrapCRLF("To: %s" % strEmails(toEmails))
    if len(ccEmails) > 0:
        dataStr += wrapCRLF("Cc: %s" % strEmails(ccEmails))
    if len(bccEmails) > 0:
        dataStr += wrapCRLF("Bcc: %s" % strEmails(bccEmails))
    dataStr += wrapCRLF("Subject: %s" % get_Subject())
    dataStr += wrapCRLF("MIME-Version: 1.0")

    if fileobj != None and filename != "":
        dataStr += wrapCRLF("Content-Type: multipart/mixed; boundary=%s" % MARKER)
        dataStr += wrapCRLF("")
        dataStr += wrapCRLF("--%s" % MARKER)
        dataStr += createMultipartEntity("text/plain", "7bit", get_Msg().rstrip(), "")
        dataStr += wrapCRLF("--%s" % MARKER)
        dataStr += createMultipartEntity("application/octet-stream", "base64", fileobj, filename)
        dataStr += wrapCRLF("--%s--" % MARKER)
        fileobj = None
        filename = ""
        showfile.set(filename)
    else:
        dataStr += wrapCRLF("")
        dataStr += wrapCRLF(get_Msg().rstrip())
        dataStr += wrapCRLF("")

    dataStr += wrapCRLF(".")

    exchangeMsg(sock, dataStr, logReq=False, expectFirst="250")


def createMultipartEntity(type, encoding, data=None, filename=""):
    result = wrapCRLF("Content-Type: %s" % type)
    result += wrapCRLF("Content-Transfer-Encoding: %s" % encoding)
    if filename != "":
        result += wrapCRLF("Content-Disposition: attachment; filename=%s" % filename)
    result += wrapCRLF("")
    if filename != "":
        result += base64.encodebytes(fileobj.read()).decode()
    else:
        result += data
    result += wrapCRLF("")
    result += wrapCRLF("")
    return result

# will throw error here
def exchangeMsg(sock: socket.socket, msg: str,
                logReq=True, logRes=True, readUntilContains="", receiveOnly=False, expectFirst="2"):
    if not receiveOnly and not msg.endswith("\r\n"):
        warning("The message '%s' does not end with CRLF" % msg)
    try:
        if not receiveOnly:
            sock.send(debugLog(msg.encode(), doPrint=logReq))

        buf = ""
        if readUntilContains != "":
            firstLineDone = False
            while not readUntilContains in buf:
                buf = debugLog(sock.recv(1024).decode(), doPrint=logRes)
                if not firstLineDone:
                    firstLineDone = True
                    throwErrorIfUnexpected(buf, expectFirst, userInput=msg)
        else:
            buf = debugLog(sock.recv(1024).decode(), doPrint=logRes)
            throwErrorIfUnexpected(buf, expectFirst, userInput=msg)
    except OSError as e:
        raise ValueError("SMTP server is not available")


def throwErrorIfUnexpected(serverResponse: str, expected: str, userInput="the email"):
    if userInput:
        if userInput.startswith("EHLO"):
            userInput = "EHLO"
        elif userInput.startswith("HELO"):
            userInput = "HELO"
        elif userInput.startswith("MAIL FROM"):
            userInput = "MAIL FROM"
        elif userInput.startswith("RCPT TO"):
            userInput = "RCPT TO"
        elif userInput.startswith("DATA"):
            userInput = "DATA"
        elif userInput.startswith("QUIT"):
            userInput = "QUIT"
        else: userInput = "the email"
    else: userInput = "the email"
    if not serverResponse.startswith(expected):
        raise ValueError("Failed in sending %s\n%s" % (userInput, serverResponse))


def parseEmailList(line: str, type: str, retNoneIfError=False, required=False):
    line = line.strip()
    if required and line == "":
        alertbox("Must input %s field" % type)
        return None if retNoneIfError else []
    elif line == "":
        return []

    if not ("," in line):
        if not echeck(line):
            alertbox("Invalid %s: Email - %s" % (type, line))
            return None if retNoneIfError else []
        return [line]

    emails = line.split(",")
    for email in emails:
        if not echeck(email):
            alertbox("Invalid %s: Email - %s" % (type, email))
            return None if retNoneIfError else []
    return emails


def strEmails(emails: list[str]):
    result = ""
    for email in emails:
        result += email + ", "
    if result != "":
        result = result[0:-2]
    return result.strip()


def wrapCRLF(msg):
    return "%s\r\n" % msg


def debugLog(msg, doPrint=False):
    if not doPrint:
        return msg
    if isinstance(msg, bytes):
        print("[Debug] %s" % msg.decode(), end="")
    else:
        print("[Debug] %s" % str(msg), end="")
    return msg


def warning(msg):
    print("[Warn] %s" % msg)

############################
###     END of SMTP      ###
############################

#
# Utility functions
#

# This set of functions is for getting the user's inputs


def get_TO():
    return tofield.get()


def get_CC():
    return ccfield.get()


def get_BCC():
    return bccfield.get()


def get_Subject():
    return subjfield.get()


def get_Msg():
    return SendMsg.get(1.0, END)

# This function checks whether the input is a valid email


def echeck(email):
    regex = '^([A-Za-z0-9]+[.\-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
    if (re.fullmatch(regex, email)):
        return True
    else:
        return False

# This function displays an alert box with the provided message


def alertbox(msg):
    messagebox.showwarning(message=msg, icon='warning',
                           title='Alert', parent=win)

# This function calls the file dialog for selecting the attachment file.
# If successful, it stores the opened file object to the global
# variable fileobj and the filename (without the path) to the global
# variable filename. It displays the filename below the Attach button.


def do_Select():
    global fileobj, filename
    if fileobj:
        fileobj.close()
    fileobj = None
    filename = ''
    filepath = filedialog.askopenfilename(parent=win)
    if (not filepath):
        return
    print(filepath)
    if sys.platform.startswith('win32'):
        filename = pathlib.PureWindowsPath(filepath).name
    else:
        filename = pathlib.PurePosixPath(filepath).name
    try:
        fileobj = open(filepath, 'rb')
    except OSError as emsg:
        print('Error in open the file: %s' % str(emsg))
        fileobj = None
        filename = ''
    if (filename):
        showfile.set(filename)
    else:
        alertbox('Cannot open the selected file')

#################################################################################
# Do not make changes to the following code. They are for the UI                 #
#################################################################################


#
# Set up of Basic UI
#
win = Tk()
win.title("EmailApp")

# Special font settings
boldfont = font.Font(weight="bold")

# Frame for displaying connection parameters
frame1 = ttk.Frame(win, borderwidth=1)
frame1.grid(column=0, row=0, sticky="w")
ttk.Label(frame1, text="SERVER", padding="5").grid(column=0, row=0)
ttk.Label(frame1, text=SERVER, foreground="green",
          padding="5", font=boldfont).grid(column=1, row=0)
ttk.Label(frame1, text="PORT", padding="5").grid(column=2, row=0)
ttk.Label(frame1, text=str(SPORT), foreground="green",
          padding="5", font=boldfont).grid(column=3, row=0)

# Frame for From:, To:, CC:, Bcc:, Subject: fields
frame2 = ttk.Frame(win, borderwidth=0)
frame2.grid(column=0, row=2, padx=8, sticky="ew")
frame2.grid_columnconfigure(1, weight=1)
# From
ttk.Label(frame2, text="From: ", padding='1', font=boldfont).grid(
    column=0, row=0, padx=5, pady=3, sticky="w")
fromfield = StringVar(value=YOUREMAIL)
ttk.Entry(frame2, textvariable=fromfield, state=DISABLED).grid(
    column=1, row=0, sticky="ew")
# To
ttk.Label(frame2, text="To: ", padding='1', font=boldfont).grid(
    column=0, row=1, padx=5, pady=3, sticky="w")
tofield = StringVar()
ttk.Entry(frame2, textvariable=tofield).grid(column=1, row=1, sticky="ew")
# Cc
ttk.Label(frame2, text="Cc: ", padding='1', font=boldfont).grid(
    column=0, row=2, padx=5, pady=3, sticky="w")
ccfield = StringVar()
ttk.Entry(frame2, textvariable=ccfield).grid(column=1, row=2, sticky="ew")
# Bcc
ttk.Label(frame2, text="Bcc: ", padding='1', font=boldfont).grid(
    column=0, row=3, padx=5, pady=3, sticky="w")
bccfield = StringVar()
ttk.Entry(frame2, textvariable=bccfield).grid(column=1, row=3, sticky="ew")
# Subject
ttk.Label(frame2, text="Subject: ", padding='1', font=boldfont).grid(
    column=0, row=4, padx=5, pady=3, sticky="w")
subjfield = StringVar()
ttk.Entry(frame2, textvariable=subjfield).grid(column=1, row=4, sticky="ew")

# frame for user to enter the outgoing message
frame3 = ttk.Frame(win, borderwidth=0)
frame3.grid(column=0, row=4, sticky="ew")
frame3.grid_columnconfigure(0, weight=1)
scrollbar = ttk.Scrollbar(frame3)
scrollbar.grid(column=1, row=1, sticky="ns")
ttk.Label(frame3, text="Message:", padding='1', font=boldfont).grid(
    column=0, row=0, padx=5, pady=3, sticky="w")
SendMsg = Text(frame3, height='10', padx=5, pady=5)
SendMsg.grid(column=0, row=1, padx=5, sticky="ew")
SendMsg.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=SendMsg.yview)

# frame for the button
frame4 = ttk.Frame(win, borderwidth=0)
frame4.grid(column=0, row=6, sticky="ew")
frame4.grid_columnconfigure(1, weight=1)
Sbutt = Button(frame4, width=5, relief=RAISED, text="SEND", command=do_Send).grid(
    column=0, row=0, pady=8, padx=5, sticky="w")
Atbutt = Button(frame4, width=5, relief=RAISED, text="Attach",
                command=do_Select).grid(column=1, row=0, pady=8, padx=10, sticky="e")
showfile = StringVar()
ttk.Label(frame4, textvariable=showfile).grid(
    column=1, row=1, padx=10, pady=3, sticky="e")

win.mainloop()
