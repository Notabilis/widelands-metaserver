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

# Logs in with the given name. If a password is given, try a registered login.
# If expName or expRang is given, check the result
# Does a legacy login
def login_legacy(name, pwd="", expName="", expRang=""):
    # Should result in: "\x00\x25LOGIN\x000\x00Pete\x00test[r1]\x00false\x00abcdef\x00"
    c = Conn()
    c.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.s.connect((TCP_IP, TCP_PORT))
    msg="LOGIN\x000\x00"+name+"\x00test[r1]\x00"
    if pwd == "":
        msg+="false\x00"
    else:
        msg+="true\x00"+pwd+"\x00"
    send_with_length(c.s, msg)
    # Login request send
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
            while True:
                try:
                    data = s.recv(BUFFER_SIZE)
                except socket.error:
                    break
                if not data:
                    break
                lines = data.split('\x00')
                for line in lines:
                    if line[1:] == "PING":
                        send_with_length(s, "PONG")

        thread.start_new_thread(t, (self.s,))

# The same again as the other file, but with a legacy client

next_test("Unregistered login")
c1 = login_legacy("testuserB", "", "testuserB", "UNREGISTERED")
c1.close()

next_test("Registered login")
c1 = login_legacy("testuser", "test", "testuser", "REGISTERED")
c1.close()

next_test("Unregistered login, trying a registered (=reserved) user name")
c1 = login_legacy("testuser", "", "testuser1", "UNREGISTERED")
c1.close()

next_test("Two unregistered logins for the same name")
c1 = login_legacy("testuserC", "", "testuserC", "UNREGISTERED")
c1.pingpongthread()
c2 = login_legacy("testuserC", "", "testuserC1", "UNREGISTERED")
c2.close()
c1.close()

next_test("Two registered logins for the same name")
c1 = login_legacy("testuser", "test", "testuser", "REGISTERED")
c1.pingpongthread()
c2 = login_legacy("testuser", "test", "testuser1", "UNREGISTERED")
c2.close()
c1.close()

next_test("Unregistered login after registered login with the same name")
c1 = login_legacy("testuser", "test", "testuser", "REGISTERED")
c1.pingpongthread()
c2 = login_legacy("testuser", "", "testuser1", "UNREGISTERED")
c2.close()
c1.close()

print "Success!"
