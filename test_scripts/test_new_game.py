#!/usr/bin/env python2

import socket
import string
import hashlib
import random
import sys
import thread
import time

# No error handling on purpose
# Assuming a newly started wlms instance

TCP_IP = '127.0.0.1'
TCP_IP6 = '::1'
TCP_PORT = 7395
BUFFER_SIZE = 4096

TEST_NUMBER = 1

def next_test(text):
    time.sleep(1)
    global TEST_NUMBER
    print("Test " + str(TEST_NUMBER) + ": " + text)
    TEST_NUMBER += 1

def sha1(str):
    m = hashlib.sha1()
    m.update(str)
    return m.hexdigest()

def send_with_length(s, msg):
    l = len(msg)
    # Too lazy to support greater lengths
    assert l < 250
    s.send("\x00"+chr(l + 2)+msg)

def expect(got, should):
    if got != should:
        print "Got unexpected data, received '" + got + "'; expected '" + should + "'"
    assert got == should

def unexpect(got, should):
    if got == should:
        print "Got unexpected data, received '" + got + "'; expected something else"
    assert got != should

# Logs in with the given name. If a password is given, try a registered login.
# If expName or expRang is given, check the result
def login(name, pwd="", expName="", expRang=""):
    # Should result in: "\x00\x25LOGIN\x004\x00Pete\x00test[r1]\x00false\x00abcdef\x00"
    c = Conn()
    c.s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    c.s.connect((TCP_IP6, TCP_PORT))
    msg="LOGIN\x004\x00"+name+"\x00test[r1]\x00"
    if pwd == "":
        rand=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        c.secret = sha1(rand)
        msg+="false\x00"+c.secret+"\x00"
    else:
        c.secret = sha1(pwd)
        msg+="true\x00\x00"
    send_with_length(c.s, msg)
    # Login request send. If we have a password, expect the challenge
    if pwd != "":
        data = c.s.recv(BUFFER_SIZE)
        lines = data[2:].split('\x00')
        expect(lines[0], "PWD_CHALLENGE")
        msg = "PWD_CHALLENGE\x00" + sha1(lines[1] + c.secret) + "\x00"
        send_with_length(c.s, msg)
    if expName != "" or expRang != "":
        data = c.s.recv(BUFFER_SIZE)
        lines = data[2:].split('\x00')
        expect(lines[0], "LOGIN")
        expect(lines[1], expName)
        expect(lines[2], expRang)
    return c

class Conn:

    def close(self):
        try:
            send_with_length(self.s, "DISCONNECT\x00Beep\x00")
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
        except socket.error:
            pass

    # Warning: Answers PING requests but discards all other data
    def pingpongthread(self):
        def t(s):
            try:
                while True:
                    data = s.recv(2)
                    if not data:
                        break
                    length = ord(data[0]) * 16 + ord(data[1])
                    data = s.recv(length - 2) # -2 since the length is included in itself
                    if not data:
                        break
                    lines = data.split('\x00')
                    #for line in lines:
                        #print line
                    if lines[0] == "PING":
                        send_with_length(s, "PONG")
            except socket.error:
                pass

        thread.start_new_thread(t, (self.s,))

    def wait_for_data(self, cmd, i):
        try:
            while True:
                data = self.s.recv(2)
                if not data:
                    break
                #print ord(data[0]), ord(data[1])
                length = ord(data[0]) * 16 + ord(data[1])
                #print length
                data = self.s.recv(length - 2) # -2 since the length is included in itself
                if not data:
                    break
                lines = data.split('\x00')
                #for line in lines:
                    #print line
                if lines[0] == "PING":
                    send_with_length(self.s, "PONG")
                elif lines[0] == cmd:
                    return lines[i]
        except socket.error:
            pass

class Game:

    def __init__(self, name, pwd):
        self.s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.s.connect(("::1", 7397))
        self.s.send("\x01\x01"+name+"\x00" + pwd + "\x00") #Hello, Version, GameName, Response
        # Check whether we receive the expected kWelcome
        r = self.s.recv(1)
        # Received anything at all?
        unexpect(r, "")
        # Received kWelcome? (Adding "0" to make the output readable)
        expect(chr(2 + ord("0")), chr(ord(r) + ord("0")))

    def close(self):
        try:
            self.s.send("\x03NORMAL\x00") #Disconnect, Reason
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
        except socket.error:
            pass

next_test("Unregistered login")
c1 = login("testuserB", "", "testuserB", "UNREGISTERED")
send_with_length(c1.s, "GAME_OPEN\x00MyGame\x00")
challenge = c1.wait_for_data("GAME_OPEN", 1)
g = Game("MyGame", sha1(challenge + c1.secret))
# Without the sleep the log messages are messed up
time.sleep(0.1)
g.close()
c1.close()

next_test("Registered login")
c1 = login("testuser", "test", "testuser", "REGISTERED")
send_with_length(c1.s, "GAME_OPEN\x00MyGame\x00")
challenge = c1.wait_for_data("GAME_OPEN", 1)
g = Game("MyGame", sha1(challenge + c1.secret))
# Without the sleep the log messages are messed up
time.sleep(0.1)
g.close()
c1.close()

next_test("Downgrade login")
c1 = login("testuser", "test", "testuser", "REGISTERED")
c1.pingpongthread()
c2 = login("testuser", "test", "testuser1", "UNREGISTERED")
# Oh no, a totally unexpected downgrade! ;)
#c2.secret = sha1("testuser1" + c2.secret)
send_with_length(c2.s, "GAME_OPEN\x00MyGame\x00")
challenge = c2.wait_for_data("GAME_OPEN", 1)
g = Game("MyGame", sha1(challenge + c2.secret))
# Without the sleep the log messages are messed up
time.sleep(0.1)
g.close()
c2.close()
c1.close()

# 30s for game timeout

# TODO: maybe testing clashes with IRC, maybe creating games
# TODO: Remove TELL_IP command
print "Success!"
