# Copyright (c) 2012 CefPython Authors. All rights reserved.
# License: New BSD License.
# Website: http://code.google.com/p/cefpython/

import win32gui
import win32con
import win32api
import time
import math
import os
import sys
import re

__debug = False
__windows = {} # windowID(int): className

def GetRealPath(file=None):
	
	# This function is defined in 2 files: cefpython.pyx and cefwindow.py, if you make changes edit both files.
	# If file is None return current directory, without trailing slash.
	if file is None: file = ""
	if file.find("/") != 0 and file.find("\\") != 0 and not re.search(r"^[a-zA-Z]+:[/\\]", file):
		# not re.search(r"^[a-zA-Z]+:[/\\]", file)
		# == not (D:\\ or D:/ or http:// or ftp:// or file://)
		if hasattr(sys, "frozen"): path = os.path.dirname(sys.executable)
		elif "__file__" in globals(): path = os.path.dirname(os.path.realpath(__file__))
		else: path = os.getcwd()
		path = path + os.sep + file
		path = re.sub(r"[/\\]+", re.escape(os.sep), path)
		path = re.sub(r"[/\\]+$", "", path)
		return path
	return file

def CreateWindow(title, className, width, height, xpos=None, ypos=None, icon=None, windowProc=None):

	"""
	for key in __windows:
		if __windows[key] == className:
			raise Exception("There was already created a window with that className: %s."
				"Each created window must have an unique className." % className)			
	"""

	if not windowProc:
		windowProc = {win32con.WM_CLOSE: WM_CLOSE}

	bigIcon = ""
	smallIcon = ""

	if icon:
		icon = GetRealPath(icon)
		
		# Load small and big icon.
		# WNDCLASSEX (along with hIconSm) is not supported by pywin32, 
		# we need to use WM_SETICON message after window creation.
		
		# http://stackoverflow.com/questions/2234988/how-to-set-hicon-on-a-window-ico-with-multiple-sizes
		# http://blog.barthe.ph/2009/07/17/wmseticon/
		
		bigX = win32api.GetSystemMetrics(win32con.SM_CXICON)
		bigY = win32api.GetSystemMetrics(win32con.SM_CYICON)
		bigIcon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, bigX, bigY, win32con.LR_LOADFROMFILE)
		smallX = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
		smallY = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
		smallIcon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, smallX, smallY, win32con.LR_LOADFROMFILE)

	wndclass = win32gui.WNDCLASS()
	wndclass.hInstance = win32api.GetModuleHandle(None)
	wndclass.lpszClassName = className
	wndclass.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
	# win32con.CS_GLOBALCLASS
	wndclass.hbrBackground = win32con.COLOR_WINDOW
	wndclass.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
	wndclass.lpfnWndProc = windowProc

	#noinspection PyUnusedLocal
	atomclass = win32gui.RegisterClass(wndclass)

	if __debug:
		print("win32gui.RegisterClass(wndclass)")
		print("GetLastError(): %s" % GetLastError())

	if xpos is None or ypos is None:
		# Center window on the screen.
		if __debug:
			print("Centering window on the screen.")
		screenx = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
		screeny = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
		xpos = int(math.floor((screenx - width) / 2))
		ypos = int(math.floor((screeny - height) / 2))
		if xpos < 0: xpos = 0
		if ypos < 0: ypos = 0

	windowID = win32gui.CreateWindow(className, title,
			win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN | win32con.WS_VISIBLE,
			xpos, ypos, width, height, # xpos, ypos, width, height
			0, 0, wndclass.hInstance, None)
	__windows[windowID] = className

	if icon:
		if bigIcon:
			win32api.SendMessage(windowID, win32con.WM_SETICON, win32con.ICON_BIG, bigIcon)
		if smallIcon:
			win32api.SendMessage(windowID, win32con.WM_SETICON, win32con.ICON_SMALL, smallIcon)
	
	if __debug:
		print("windowID=%s" % windowID)

	return windowID


# Memory error when calling win32gui.DestroyWindow()
# after we called cefpython.CloseBrowser()

def DestroyWindow(windowID):
	
	win32gui.DestroyWindow(windowID)
	#className = GetWindowClassName(windowID)
	#win32gui.UnregisterClass(className, None)
	#del __windows[windowID] # Let window with this className be created again.
	

def GetWindowClassName(windowID):

	for key in __windows:
		if key == windowID:
			return __windows[key]

def MoveWindow(windowID, xpos=None, ypos=None, width=None, height=None, center=None):

	(left, top, right, bottom) = win32gui.GetWindowRect(windowID)
	if xpos is None and ypos is None:
		xpos = left
		ypos = top
	if width is None and height is None:
		width = right - left
		height = bottom - top
	# Case: only ypos provided
	if xpos is None and ypos is not None:
		xpos = left
	if ypos is None and xpos is not None:
		ypos = top
	# Case: only height provided
	if not width:
		width = right - left
	if not height:
		height = bottom - top
	if center:
		screenx = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
		screeny = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
		xpos = int(math.floor((screenx - width) / 2))
		ypos = int(math.floor((screeny - height) / 2))
		if xpos < 0: xpos = 0
		if ypos < 0: ypos = 0
	win32gui.MoveWindow(windowID, xpos, ypos, width, height, 1)


#noinspection PyUnusedLocal
def WM_CLOSE(windowID, msg, wparam, lparam):
	
	DestroyWindow(windowID)
	win32gui.PostQuitMessage(0)


def GetLastError():
	
	code = win32api.GetLastError()
	return "(%d) %s" % (code, win32api.FormatMessage(code))

#noinspection PyUnusedLocal
def MessageLoop(className):
	
	while not win32gui.PumpWaitingMessages():
		time.sleep(0.001)


if __name__ == "__main__":
	
	__debug = True
	hwnd = CreateWindow("Test window", "testwindow", 800, 600)
	MessageLoop("testwindow")