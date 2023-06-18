#!/usr/bin/env python3

PROGRAM = 'wav-player.py'
VERSION = '2.306.181'
CONTACT = 'bright.tiger@mail.com' # michael nagy for bobproducts.com

#--------------------------------------------------------------------
# wav-player.py
#--------------------------------------------------------------------
# play wav files which match WavPattern one after the next when the
# configured GPIO button is pressed.  we expect to be started at
# boot by the cron facility:
#
#   @reboot ~/wav.player.py
#
# we also expect the pulse-audio output device to be set to the usb
# output, which is also done via cron:
#
#   @reboot /usr/bin/pacmd set-default-sink 1
#
# use this command to verify the usb device index if necessary:
#
#   pacmd list-sinks | grep 'index:\|name:'
#
# wav files are played by running vlc synchronously (we wait for vlc
# to terminate before continuing).  if vlc is already running when
# we want to play a wav file, that indicates that a cron job or and
# xkeybind macro is active.  in this instance we have priority, so
# we always killall vlc before starting our playback.
#--------------------------------------------------------------------

WavPattern = '/home/pi/Shows/show*.wav'

GpioButtonTrigger =  4 # pulled up, take low to trigger

GpioOutputPlaying = 17 # high when playing
GpioOutputIdle    = 27 # high when idle

import os, sys, glob, time
import RPi.GPIO as GPIO
from syslog import syslog

#----------------------------------------------------------------------
# debounce the gpio input button - it is pulled high, so low means it
# is pressed.  we poll every millisecond, and require it to be in the
# desired state for 100 continguous polls, or 0.1 seconds
#----------------------------------------------------------------------

def WaitForButton(Pressed):
  Value = 0
  while Value < 100:
    if Pressed:
      InDesiredState = not GPIO.input(GpioButtonTrigger) # button is pressed
    else:
      InDesiredState =     GPIO.input(GpioButtonTrigger) # button is released
    if InDesiredState:
      Value += 1
    else:
      Value = 0
    time.sleep(0.001)

#----------------------------------------------------------------------
# log a message to the console and /var/log/syslog
#----------------------------------------------------------------------

def Log(Message):
  print('%s' % (Message))
  syslog(Message)

#----------------------------------------------------------------------
# play a wave file using a new instance of MediaPlayer, and hopefully
# deallocate that instance upon return
#----------------------------------------------------------------------

def PlayWavFile(WavFile):
  time.sleep(1.0)
  WaitForButton(False)
  Log('IDLE')
  GPIO.output(GpioOutputIdle, 1)
  WaitForButton(True)
  GPIO.output(GpioOutputIdle, 0)
  Log('PLAY %s' % (WavFile))
  GPIO.output(GpioOutputPlaying, 1)
  try:
    os.system("killall vlc")
    os.system("vlc %s --play-and-exit" % (WavFile))
    Log('DONE %s' % (WavFile))
  except:
    Log("*** ERROR 3: try: sudo 'apt-get install pulseaudio'")

#----------------------------------------------------------------------
# loop forever waiting for button presses
#----------------------------------------------------------------------

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GpioButtonTrigger, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GpioOutputPlaying, GPIO.OUT, )
GPIO.setup(GpioOutputIdle   , GPIO.OUT, )
GPIO.output(GpioOutputPlaying, 0)
GPIO.output(GpioOutputIdle   , 1)

Log('START %s %s' % (PROGRAM, VERSION))
try:
  WavFiles = glob.glob(WavPattern)
  if WavFiles:
    WavFiles = sorted(WavFiles)
    Log("READ %d FILES MATCHING '%s'" % (len(WavFiles), WavPattern))
    while True:
      Log('START SEQUENCE')
      for WavFile in WavFiles:
        PlayWavFile(WavFile)
  else:
    Log("*** ERROR 2: NO FILES MATCH '%s'" % (WavPattern))
except:
  if not WavFiles:
    Log("*** ERROR 1: NO FILES MATCH '%s'" % (WavPattern))

GPIO.output(GpioOutputPlaying, 0)
GPIO.output(GpioOutputIdle   , 1)
Log('EXIT')

#--------------------------------------------------------------------
# end
#--------------------------------------------------------------------
