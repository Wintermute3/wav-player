#!/usr/bin/env python3

PROGRAM = 'wav-player.py'
VERSION = '1.909.181'
CONTACT = 'bright.tiger@mail.com' # michael nagy for bobproducts.com

#--------------------------------------------------------------------
# wav-player.py
#--------------------------------------------------------------------
# play wav files which match WavPattern one after the next when the
# configured GPIO button is pressed.  we expect to be started and
# controlled by a systemd unit file with watchdog features enabled.
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
# set up vlc and loop forever waiting for button presses
#----------------------------------------------------------------------

try:
  import vlc
  vlc.Instance("--vout none") # seemed to help select proper output device, not sure why
except:
  Log('*** ERROR 0: python-vlc not found!')
  Log("             try: 'sudo pip3 install python-vlc'")
  os._exit(1)

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
        time.sleep(1.0)
        WaitForButton(False)
        Log('IDLE')
        GPIO.output(GpioOutputIdle, 1)
        WaitForButton(True)
        GPIO.output(GpioOutputIdle, 0)
        Log('PLAY %s' % (WavFile))
        GPIO.output(GpioOutputPlaying, 1)
        try:
          player = vlc.MediaPlayer(WavFile)
          player.play()
          while player.get_state() != 6: # ENDED
            time.sleep(0.1) # wait for end of show track
          GPIO.output(GpioOutputPlaying, 0)
          Log('DONE %s' % (WavFile))
        except:
          Log('*** ERROR 3: VLC EXCEPTION')
          Log("             try: 'sudo apt-get install pulseaudio'")
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
