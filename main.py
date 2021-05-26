#!/usr/bin/env python

from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, TextNode
from panda3d.core import PointLight, AmbientLight, DirectionalLight
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.interval.SoundInterval import SoundInterval
from direct.gui.DirectSlider import DirectSlider
from direct.gui.DirectButton import DirectButton
from direct.interval.MetaInterval import Parallel
from direct.interval.LerpInterval import LerpHprInterval
from direct.task.Task import Task
import sys

import os

import serial
import serial.tools.list_ports

import json

SERIAL_ACTIVE = True
USE_FADE_OUT = True
FADE_OUT_SPEED = 5
USE_FADE_IN = True
FADE_IN_SPEED = 5
PRINT_NOTES = False
SETS_FOLDERS = ["sounds"]
SETS_SWITCH_NOTES = []

with open("config.json", encoding='utf-8') as configFile:
    config = json.load(configFile)

    SERIAL_ACTIVE = config["serialActive"]
    USE_FADE_OUT = config["useFadeOut"]
    FADE_OUT_SPEED = config["fadeOutSpeed"]
    USE_FADE_IN = config["useFadeIn"]
    FADE_IN_SPEED = config["fadeInSpeed"]
    PRINT_NOTES = config["afficherNote"]
    SETS_FOLDERS = config["setsFolders"]
    SETS_SWITCH_NOTES = config["setsSwitchNotes"]


def files(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file

# Create an instance of ShowBase, which will open a window and set up a
# scene graph and camera.
base = ShowBase()

class MusicBox(DirectObject):
    def __init__(self):
        # Set up the key input
        self.accept('escape', sys.exit)
        self.accept('1', self.note1)
        self.accept('1-up', self.note1Up)
        self.accept('2', self.note2)
        self.accept('2-up', self.note2Up)
        self.accept('3', self.note3)
        self.accept('3-up', self.note3Up)
        self.accept('4', self.note4)
        self.accept('4-up', self.note4Up)
        self.accept('5', self.note5)
        self.accept('5-up', self.note5Up)
        self.accept('6', self.note6)
        self.accept('6-up', self.note6Up)
        self.accept('7', self.note7)
        self.accept('7-up', self.note7Up)
        self.accept('8', self.note8)
        self.accept('8-up', self.note8Up)
        self.accept('9', self.note9)
        self.accept('9-up', self.note9Up)
        self.accept('0', self.note0)
        self.accept('0-up', self.note0Up)

        # Fix the camera position
        base.disableMouse()

        self.nbNotes = 49
        self.notesStates = [False] * self.nbNotes


        for i in range(self.nbNotes):
            self.notesStates[i] = False

        self.currentSet = 0
        self.notes = []

        try:    
            for folder in SETS_FOLDERS:
                currentNotes = []
                print("Processing folder {}".format(folder))
                for file in files("./" + folder +"/"):
                    note = loader.loadSfx("./" + folder +"/" +file)
                    print(file)
                    if file.find("_c.") >= 0:
                        note.setLoopCount(0)
                    currentNotes.append(note)

                self.notes.append(currentNotes)

        except:
            print("Impossible de charger les sons")


        for noteSet in self.notes:
            print("{} sons chargés".format(len(noteSet)))

        port = "COM3"

        foundPorts = serial.tools.list_ports.comports()

        for info in foundPorts:
            print(info)
            hwid = info.hwid.split(" ") 
            
            if len(hwid) > 1:
                print("hwid1 " + hwid[1])
                if hwid[1] == "VID:PID=1A86:7523":
                    port = info.device
                    break

        self.initialized = False

        try:
            if SERIAL_ACTIVE:
                print("Tentative d'ouverture du port " + port)
                self.serialPort = serial.Serial(port, 115200)
                self.initialized = True
                
                print("Initialization de la communication réussie")                
            else:
                print("Communication désactivée")

            taskMgr.remove("update")
            self.mainLoop = taskMgr.add(self.update, "update")
        except Exception as e:
            print(e)
            self.initialized = False
            print("Impossible de détecter une communication")
            quit()

    def update(self, task):
        dt = globalClock.getDt()

        if SERIAL_ACTIVE:
            msg = self.serialPort.readline()
            self.serialPort.flushInput()

            if len(msg) == 51: #49 notes + \r + \n
   
                strMsg = "".join(map(chr, msg))

                values = list(strMsg)

                for i in range(len(values) - 2): #51 - 2 = 49
                    if i < len(self.notes[self.currentSet]):
                        if values[i] == '1':
                            if self.notesStates[i] == False:
                                self.notesStates[i] = True;

                                if not self.tryChangeSet(i):
                                    if USE_FADE_IN: 
                                        self.notes[self.currentSet][i].setVolume(0)
                                    else:
                                        self.notes[self.currentSet][i].setVolume(1)

                                    self.notes[self.currentSet][i].play()

                                    if PRINT_NOTES:
                                        print("Note: " + str(i + 1))
                        else:
                            if self.notesStates[i] == True:
                                if (not USE_FADE_OUT):
                                    self.notes[self.currentSet][i].stop()
                                self.notesStates[i] = False
                    else:
                        break

        if USE_FADE_OUT:
            for i in range(len(self.notes[self.currentSet])):
                if self.notesStates[i] == False:
                    if self.notes[self.currentSet][i].getVolume() > 0:
                        newValue = self.notes[self.currentSet][i].getVolume() - FADE_OUT_SPEED * dt
                        if newValue < 0:
                            self.notes[self.currentSet][i].setVolume(0)
                        else:
                            self.notes[self.currentSet][i].setVolume(newValue)

        if USE_FADE_IN:
            for i in range(len(self.notes[self.currentSet])):
                if self.notesStates[i] == True:
                    if self.notes[self.currentSet][i].getVolume() < 1:
                        newValue = self.notes[self.currentSet][i].getVolume() + FADE_IN_SPEED * dt
                        if newValue > 1:
                            self.notes[self.currentSet][i].setVolume(1)
                        else:
                            self.notes[self.currentSet][i].setVolume(newValue)
                
        return Task.cont

    def tryChangeSet(self, noteIndex):
        for j in range(0, len(SETS_SWITCH_NOTES)):
            if noteIndex == SETS_SWITCH_NOTES[j]:
                self.note0Up()
                self.currentSet = j
                #print("Set change for {}".format(j))
                return True

        return False

    def note1(self):
        if self.tryChangeSet(1):
            return

        if self.notesStates[0] == False:
            if USE_FADE_IN: 
                self.notes[self.currentSet][0].setVolume(0)
            else:
                self.notes[self.currentSet][0].setVolume(1)
            self.notes[self.currentSet][0].play()
            self.notesStates[0] = True

    def note2(self):
        if self.tryChangeSet(2):
            return

        if self.notesStates[1] == False:
            if USE_FADE_IN: 
                self.notes[self.currentSet][1].setVolume(0)
            else:
                self.notes[self.currentSet][1].setVolume(1)
            self.notes[self.currentSet][1].play()
            self.notesStates[1] = True

    def note3(self):
        if self.tryChangeSet(3):
            return

        if self.notesStates[2] == False:
            if USE_FADE_IN: 
                self.notes[self.currentSet][2].setVolume(0)
            else:
                self.notes[self.currentSet][2].setVolume(1)
            self.notes[self.currentSet][2].play()
            self.notesStates[2] = True

    def note4(self):
        if self.tryChangeSet(4):
            return

        if self.notesStates[3] == False: 
            if USE_FADE_IN: 
                self.notes[self.currentSet][3].setVolume(0)
            else:
                self.notes[self.currentSet][3].setVolume(1)
            self.notes[self.currentSet][3].play()
            self.notesStates[3] = True

    def note5(self):
        if self.tryChangeSet(5):
            return

        if self.notesStates[4] == False: 
            if USE_FADE_IN: 
                self.notes[self.currentSet][4].setVolume(0)
            else:
                self.notes[self.currentSet][4].setVolume(1)
            self.notes[self.currentSet][4].play()
            self.notesStates[4] = True

    def note6(self):
        print("Playing on set {}".format(self.currentSet))

        if self.notesStates[5] == False: 
            if USE_FADE_IN: 
                self.notes[self.currentSet][5].setVolume(0)
            else:
                self.notes[self.currentSet][5].setVolume(1)
            self.notes[self.currentSet][5].play()
            self.notesStates[5] = True

    def note7(self):
        if self.notesStates[6] == False: 
            if USE_FADE_IN: 
                self.notes[self.currentSet][6].setVolume(0)
            else:
                self.notes[self.currentSet][6].setVolume(1)
            self.notes[self.currentSet][6].play()
            self.notesStates[6] = True

    def note8(self):
        if self.notesStates[7] == False: 
            if USE_FADE_IN: 
                self.notes[self.currentSet][7].setVolume(0)
            else:
                self.notes[self.currentSet][7].setVolume(1)
            self.notes[self.currentSet][7].play()
            self.notesStates[7] = True

    def note9(self):
        if self.notesStates[8] == False: 
            if USE_FADE_IN: 
                self.notes[self.currentSet][8].setVolume(0)
            else:
                self.notes[self.currentSet][8].setVolume(1)
            self.notes[self.currentSet][8].play()
            self.notesStates[8] = True

    def note0(self):
        for note in self.notes[self.currentSet]:
            note.setVolume(1)
            note.play()
        for i in range(len(self.notesStates)):
            self.notesStates[i] = True

    def note1Up(self):
        self.notesStates[0] = False


    def note2Up(self):
        self.notesStates[1] = False

    def note3Up(self):
        self.notesStates[2] = False

    def note4Up(self):
        self.notesStates[3] = False

    def note5Up(self):
        self.notesStates[4] = False

    def note6Up(self):
        self.notesStates[5] = False

    def note7Up(self):
        self.notesStates[6] = False

    def note8Up(self):
        self.notesStates[7] = False

    def note9Up(self):
        self.notesStates[8] = False

    def note0Up(self):
        if not USE_FADE_OUT:
            for note in self.notes[self.currentSet]:
                note.stop()
        for i in range(len(self.notesStates)):
            self.notesStates[i] = False


mb = MusicBox()
base.run()
