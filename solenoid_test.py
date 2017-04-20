#!/usr/bin/env python
#----------------------------------------------------------------------------
# Name:
# Purpose:
#
# Author:       Gordon Su
# Contact:
#----------------------------------------------------------------------------
#
#
# History:      23 Jan 2017     initial release
#
#
#
#
#
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import wx
import re
import time
import serial
import easygui
import threading
from wx.lib.wordwrap import wordwrap


GUI_ROW01       = 10    # title
GUI_ROW02       = 30    # ch 0
GUI_ROW03       = 50
GUI_ROW04       = 70
GUI_ROW05       = 90
GUI_ROW06       = 110
GUI_ROW07       = 130
GUI_ROW08       = 150
GUI_ROW09       = 170
GUI_ROW10       = 190
GUI_ROW11       = 210   # ch 10
GUI_ROW12       = 250   # cycle mode
GUI_ROW13       = 310   # error
GUI_ROW14       = 400   # error

GUI_COLUMN01    = 10    # ch
GUI_COLUMN02    = 60    # pass cnt
GUI_COLUMN03    = 170   # fail cnt
GUI_COLUMN04    = 280   # last result
GUI_COLUMN05    = 390   #
GUI_COLUMN06    = 500   #
GUI_COLUMN07    = 600   # ch enable

INDEX_LC        = 0
INDEX_EC        = 1
INDEX_LR        = 2
INDEX_ON        = 3
INDEX_OF        = 4

SB_LOOPCNT      = 0
SB_TOTALCNT     = 3
SB_TIME         = 1
SB_STATUS       = 2


class MyApp(wx.App):
    def OnInit(self):
        if self.SerialSearch() == True:
            self.frame = MyFrame(None)
            self.SetTopWindow(self.frame)
            self.frame.Show()
            return True
        else:
            return False

    def SerialSearch(self):
        self.port_list = []
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            des = str(p)
            index = des.find(' - Stellaris Virtual Serial Port')
            if index != -1:
                self.port_list.append(des[:index])

        if self.port_list == []:
            easygui.msgbox("Connect the board first and re-run this program", title="Error")
            self.Destroy() # close windows, exit app
            return False
        else:
            return True



class CustomStatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)

        # This status bar has three fields
        self.SetFieldsCount(3)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-2, -2, -1])
        self.sizeChanged = False

        # Field 0 ... just text
        self.ts = ['0', '00:00:00', 'idle', '4294967296']

        self.SetStatusText('Progress:   ' + self.ts[SB_LOOPCNT] + ' / ' + self.ts[SB_TOTALCNT], 0)
        self.SetStatusText('Time Elapsed:   ' + self.ts[SB_TIME], 1)
        self.SetStatusText('Status:   ' + self.ts[SB_STATUS], 2)

    def SetVal(self, index, val):
        self.ts[index] = val
        if index == 0:
            self.SetStatusText('Progress:   ' + self.ts[SB_LOOPCNT] + ' / ' + self.ts[SB_TOTALCNT], 0)
        elif index == 1:
            self.SetStatusText('Time Elapsed:   ' + self.ts[SB_TIME], 1)
        elif index == 2:
            self.SetStatusText('Status:   ' + self.ts[SB_STATUS], 2)
        elif index == 3:
            self.SetStatusText('Progress:   ' + self.ts[SB_LOOPCNT] + ' / ' + self.ts[SB_TOTALCNT], 0)

    def GetVal(self, index):
        return self.ts[index]
        #self.test_status = [r_cycle, t_duration, t_status, t_cycle]



class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title="",
        pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="MyFrame"):

        super(MyFrame, self).__init__(parent, id, title='Solenoid Test',
            size=(640, 450), style= wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)

##        self.panel = wx.Panel(self)
        self.sb = CustomStatusBar(self)
        self.SetStatusBar(self.sb)

        self.loop_all = 0
        self.SerialSearch()
        self.SerialConfig()
        self.thread = None
        self.alive = threading.Event()
        self.InitFrame()
        self.Centre()
        self.Show()
        self.InitButtons()
        self.InitRunMode()
        self.InitSolGUI()
        #self.InitStatusBar()
        #self.InitStatusSummary()
        wx.Log.SetActiveTarget(wx.LogStderr())

        # create log file in the log sub-directory
        if not os.path.exists('Log'):
            os.makedirs('Log')

        os.chdir('Log')
        t_now = time.localtime()
        self.file_name = 'Log '+str(t_now[0])+str(t_now[1])+str(t_now[2])
        fp = open(self.file_name, 'a')
        fp.close()


    def SerialConfig(self):
        self.hSerial = serial.Serial()
        self.hSerial.baudrate = 115200
        self.hSerial.bytesize = 8
        self.hSerial.stopbits = 1
        self.hSerial.parity = serial.PARITY_NONE
        self.hSerial.xonxoff = False
        #self.hSerial.timeout = 0   # non-blocking mode, return immediately
        self.hSerial.timeout = 1    # read timeout 1 sec
        self.hSerial.write_timeout = 1

        self.sSerialPortNo = ''


    def SerialSearch(self):
        self.port_list = []
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            des = str(p)
            index = des.find(' - Stellaris Virtual Serial Port')
            if index != -1:
                self.port_list.append(des[:index])


    def InitFrame(self):
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        m_about = fileMenu.Append(wx.ID_ABOUT, 'About', '')
        fileMenu.AppendSeparator()
        m_quit = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        menubar.Append(fileMenu, '&File')
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.OnAbout, m_about)
        self.Bind(wx.EVT_MENU, self.OnQuit, m_quit)
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        self.Centre()
        self.Show(True)


    def InitSolGUI(self):
        self.ch_status = []
        self.err_cnt = []
        self.lp_cnt = []
        self.en_val = []

        lc = []
        ec = []
        lr = []
        on = []
        off = []
        en = []

        wx.StaticText(self, -1, "CH",               (GUI_COLUMN01, GUI_ROW01))
        wx.StaticText(self, -1, "Loop Count",       (GUI_COLUMN02+10, GUI_ROW01))
        wx.StaticText(self, -1, "Fail Count",       (GUI_COLUMN03+10, GUI_ROW01))
        wx.StaticText(self, -1, "Last Test Result", (GUI_COLUMN04, GUI_ROW01))
        wx.StaticText(self, -1, "ON Time mS ",      (GUI_COLUMN05, GUI_ROW01))
        wx.StaticText(self, -1, "OFF Time mS ",     (GUI_COLUMN06, GUI_ROW01))
        wx.StaticText(self, -1, "EN",               (GUI_COLUMN07, GUI_ROW01))

        for i in range(0, 10):
            wx.StaticText(self, -1, str(i), (GUI_COLUMN01+2, GUI_ROW02+i*20+5))
            lc.append(wx.TextCtrl(self, -1, "", (GUI_COLUMN02, GUI_ROW02+i*20), size=(80,20), style=wx.TE_READONLY))
            ec.append(wx.TextCtrl(self, -1, "", (GUI_COLUMN03, GUI_ROW02+i*20), size=(80,20), style=wx.TE_READONLY))
            lr.append(wx.TextCtrl(self, -1, "", (GUI_COLUMN04, GUI_ROW02+i*20), size=(80,20), style=wx.TE_READONLY))
            on.append(wx.TextCtrl(self, -1, "", (GUI_COLUMN05, GUI_ROW02+i*20), size=(80,20), style=wx.TE_READONLY))
            off.append(wx.TextCtrl(self, -1, "", (GUI_COLUMN06, GUI_ROW02+i*20), size=(80,20), style=wx.TE_READONLY))
            en.append(wx.CheckBox(self, -1, "", (GUI_COLUMN07, GUI_ROW02+i*20+5)))
            en[i].Bind(wx.EVT_CHECKBOX, lambda evt, temp=i: self.OnCheckBox(evt, temp))

            self.ch_status.append([lc[i], ec[i], lr[i], on[i], off[i]])
            self.err_cnt.append(0)
            self.lp_cnt.append(0)
            self.en_val.append(False)

        en[0].SetValue(True)
        self.en_val[0] = True


    def InitRunMode(self):
        b = wx.StaticBox(self, -1, "Cycle Mode", (GUI_COLUMN01, GUI_ROW12), (350, 50))
        box1 = wx.StaticBoxSizer(b, wx.HORIZONTAL)

        self.rb1 = wx.RadioButton(self, -1, "Indefinitely", (GUI_COLUMN01+10, GUI_ROW12+25), style = wx.RB_GROUP)
        self.rb2 = wx.RadioButton(self, -1, "Once", (GUI_COLUMN01+100, GUI_ROW12+25))
        self.rb3 = wx.RadioButton(self, -1, "Cycle Count", (GUI_COLUMN01+160, GUI_ROW12+25))
        self.cc = wx.TextCtrl(self, -1, "10", (GUI_COLUMN01+250, GUI_ROW12+23), size=(70, 20))

        self.Bind(wx.EVT_RADIOBUTTON, self.EvtRunMode, self.rb1)
        self.Bind(wx.EVT_RADIOBUTTON, self.EvtRunMode, self.rb2)
        self.Bind(wx.EVT_RADIOBUTTON, self.EvtRunMode, self.rb3)

        self.cc.Enable(False)
        self.Bind(wx.EVT_TEXT, self.EvtCycleNo, self.cc)


        error_handle_list = ['Continue on Error', 'Stop on Error']
        er = wx.RadioBox(self, -1, "Error Handling Action", (GUI_COLUMN01, GUI_ROW13), wx.DefaultSize, error_handle_list, 0, wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.EvtErrorMode, er)

        self.op_mode = ['0', '0'] # [indefinitely, continue on error]


    def InitButtons(self):
        #-----------------------------------------------------------------------
        # buttons - connect, stop
        #
        self.b_start = wx.Button(self, -1, 'Start Test',(GUI_COLUMN05+20, GUI_ROW12), size=(80, 25))
        b_clear = wx.Button(self, -1, 'Clear Result',	(GUI_COLUMN05+20, GUI_ROW12+40), size=(80, 25))
        self.b_stop = wx.Button(self, -1, 'Stop Test',	(GUI_COLUMN06+20, GUI_ROW12), size=(80, 25))
        self.b_save = wx.Button(self, -1, 'Save Log',   (GUI_COLUMN06+20, GUI_ROW12+40), size=(80, 25))
        self.b_connect = wx.Button(self, -1, 'Connect',	(GUI_COLUMN06+20, GUI_ROW13+20), size=(80, 25))

        self.Bind(wx.EVT_BUTTON, self.OnStartTest, self.b_start)
        self.Bind(wx.EVT_BUTTON, self.OnStopTest, self.b_stop)
        self.Bind(wx.EVT_BUTTON, self.OnClearResult, b_clear)
        self.Bind(wx.EVT_BUTTON, self.OnSaveLog, self.b_save)
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.b_connect)

        wx.StaticText(self, -1, "COM", (GUI_COLUMN04+90, GUI_ROW13+25))
        port = wx.Choice(self, -1, (GUI_COLUMN05+20, GUI_ROW13+20), size= (80,25), choices=self.port_list)
        self.Bind(wx.EVT_CHOICE, self.EvtSerialSel, port)

        if self.port_list != []: # default selection
            port.SetStringSelection(self.port_list[0])
            self.sSerialPortNo = self.port_list[0]


    def EvtSerialSel(self, event):
        if self.port_list == []:
            easygui.msgbox("Please check board connection and re-run this program", title="Error")

        self.sSerialPortNo = event.GetString()
        #log.WriteText('EvtChoice:\n')
        #log.WriteText('EvtChoice: %s\n' % event.GetString())




    def EvtRunMode(self, event):
        if self.rb1.GetValue() == True:
            self.cc.Enable(False)
            self.op_mode[0] = '0'
            self.sb.SetVal(SB_TOTALCNT, '4294967296')
        elif self.rb2.GetValue() == True:
            self.cc.Enable(False)
            self.op_mode[0] = '1'
            self.sb.SetVal(SB_TOTALCNT, self.op_mode[0])
        elif self.rb3.GetValue() == True:
            self.cc.Enable(True)
            self.op_mode[0] = str(self.cc.GetValue())
            self.sb.SetVal(SB_TOTALCNT, self.op_mode[0])

        print self.op_mode[0]


    def EvtErrorMode(self, event):
        self.op_mode[1] = str(event.GetSelection())
        print self.op_mode[1]


    def EvtCycleNo(self, event):
        t = str(event.GetString())
        try:
            tint = int(t)
        except:
            easygui.msgbox("Invalid Number", title="Error")
        else:
            if tint >0xFFFFFFFF:
                easygui.msgbox("Number is too large", title="Error")
            else:
                self.op_mode[0] = t
                self.sb.SetVal(SB_TOTALCNT, self.op_mode[0])
                print self.op_mode[0]


    def OnCheckBox(self, event, ch_en):
        self.en_val[ch_en] = event.IsChecked()
        for i in range (0, 10):
            print self.en_val[i],
        print ""

    def OnQuit(self, e):
        """Called on application shutdown."""
        self.Destroy()                  # close windows, exit app

    def OnAbout(self, e):
        info = wx.AboutDialogInfo()
        info.Name = "Solenoid Test"
        info.Version = "1.20"
        info.Copyright = "(C) 2017 WoodBridge Electronics Pte Ltd"
        info.Description = (
            "A \"solenoid test\" is a software program that communicates\n"
            "with 10-channel solenoid control board via USB interface. \n\n"
            "Any enquiry email to:     WoodBridgeElectronics@gmail.com    \n")

        info.WebSite = ("https://github.com/woodbridgeelectronics/solenoid-test", "source code")

        wx.AboutBox(info)


    def OnCloseFrame(self, evt):
        self.Destroy()                  # close windows, exit app


    def OnClearResult(self, event):
        if self.sb.GetVal(2) == 'Running':
            easygui.msgbox("Click Stop Test first", title="Error")
        elif self.b_connect.GetLabel() == 'Connect':
            easygui.msgbox("Click Connect first", title="Error")
        else:
            self.hSerial.write(b'c a\r')

            for ch in range (0, 10):
                self.ch_status[ch][INDEX_LC].SetValue('0')
                self.ch_status[ch][INDEX_EC].SetValue('0')
                self.ch_status[ch][INDEX_EC].SetBackgroundColour('white')
                self.ch_status[ch][INDEX_EC].Refresh()

                self.ch_status[ch][INDEX_LR].SetValue('')
                self.ch_status[ch][INDEX_ON].SetValue('')
                self.ch_status[ch][INDEX_OF].SetValue('')
                self.err_cnt[ch] = 0
                self.lp_cnt[ch] = 0

            self.loop_all = 0
            self.sb.SetVal(SB_LOOPCNT, str(self.loop_all))

    def OnConnect(self, event):
        b = event.GetEventObject()
        if b.GetLabel() == 'Connect':
            self.hSerial.port = self.sSerialPortNo
            try:
                self.hSerial.open()
            except:
                easygui.msgbox(self.sSerialPortNo + " cannot be opened", title="Error")

            if self.hSerial.is_open == True:
                b.SetLabel('Connected')
                self.hSerial.write(b's a\r')
                time.sleep(0.1)
                self.hSerial.write(b'c a\r')

        else:
            self.hSerial.close()
            if self.hSerial.is_open == False:
                b.SetLabel('Connect')


    def OnStartTest(self, event):
        if self.hSerial.is_open == False:
            easygui.msgbox("Click Connect first", title="Error")
        else:
            fp = open(self.file_name, 'a')
            fp.write('\n\n\nTest started at: ' + time.asctime() + '\n')
            fp.write('==========================================\n')
            fp.write('Pass/Fail,Channel, Loop Count, Switching On (mS), Switching Off (ms)\n')
            fp.close()

            self.sb.SetVal(SB_STATUS, 'Running')
            if self.op_mode[0] == '0':
                self.sb.SetVal(SB_TOTALCNT, '4294967296')
            else:
                self.sb.SetVal(SB_TOTALCNT, self.op_mode[0])

            self.hSerial.write(b'e ' + self.op_mode[1] + b'\r')
            time.sleep(0.1)
            self.hSerial.write(b'l ' + self.op_mode[0] + b'\r')
            self.StartThread()


    def OnStopTest(self, event):
        if self.hSerial.is_open == False:
            easygui.msgbox("Click Connect first", title="Error")
        else:
            fp = open(self.file_name, 'a')
            fp.write('Test stopped at: ' + time.asctime() + '\n')
            fp.close()

            self.sb.SetVal(SB_STATUS, 'idle')
            self.hSerial.write(b's a\r')
            self.StopThread()

    def OnSaveLog(self, event):
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir='c:\\',
            defaultFile="Log.csv", wildcard="All files (*.*)|*.*", style=wx.SAVE
            )

        # This sets the default filter that the user will initially see. Otherwise,
        # the first filter in the list will be used by default.
        dlg.SetFilterIndex(2)

        # Show the dialog and retrieve the user response. If it is the OK response,
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

            fp = file(path, 'w') # Create file anew
            with open(self.file_name, 'r') as f:
                for i in f:
                    fp.write(i)
            fp.close()

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()


    def StartThread(self):
        """Start the receiver thread"""
        self.thread = threading.Thread(target=self.ComPortThread)
        #self.thread.setDaemon(1)
        self.alive.set()
        self.thread.setDaemon(True) # thread exit with parents
        self.thread.start()

    def StopThread(self):
        """Stop the receiver thread, wait until it's finished."""
        if self.thread is not None:
            self.alive.clear()          # clear alive event for thread
            self.thread.join()          # wait until thread has finished
            self.thread = None


    def ComPortThread(self):
        """\
        Thread that handles the incoming traffic. Does the basic input
        transformation (newlines) and generates an SerialRxEvent
        """
        while self.alive.isSet():
            # print "from thread while loop"
            b = self.hSerial.readline()
            if b:
                print b

                bset = re.findall(r'P,\d+,\d+,\d+,\d+', b)
                if bset != []:
                    self.UpdateGUI(bset[0].split(','))

                bset = re.findall(r'F,\d+,\d+,\d+,\d+', b)
                if bset != []:
                    self.UpdateGUI(bset[0].split(','))

                bset = re.findall(r'T,\d+', b)
                if bset != []:
                    self.UpdateGUI(bset[0].split(','))

        print "from thread exit"


    def WriteText(self, text):
        if text[-1:] == '\n':
            text = text[:-1]
        wx.LogMessage(text)



    def UpdateGUI(self, bstr):
        if bstr[0] == 'T': # time
            td = ''
            tint = int(bstr[1])
            if tint/3600 < 10:
                td = td + '0'
            td = td + str(tint/3600) + ':'
            if (tint%3600)/60 < 10:
                td = td + '0'
            td = td + str((tint%3600)/60) + ':'
            if tint%60 < 10:
                td = td + '0'
            td = td + str(tint%60)

            self.sb.SetVal(SB_TIME, td)
        elif bstr[0] == 'P' or bstr[0] == 'F':
            ch = int(bstr[1])
            lp = int(bstr[2])

            # ch enabled? new loop #?
            if self.en_val[ch] == True and self.lp_cnt[ch] != lp:
                self.lp_cnt[ch] = lp

                fp = open(self.file_name, 'a')
                fp.write(','.join(bstr)+'\n')
                fp.close

                if lp >= self.loop_all:
                    self.loop_all = lp + 1
                    self.sb.SetVal(SB_LOOPCNT, bstr[2])

                self.ch_status[ch][INDEX_ON].SetValue(bstr[3])
                self.ch_status[ch][INDEX_OF].SetValue(bstr[4])

                if bstr[0] == 'F':
                    self.err_cnt[ch] = self.err_cnt[ch] + 1
                    self.ch_status[ch][INDEX_EC].SetValue(str(self.err_cnt[ch]))
                    self.ch_status[ch][INDEX_EC].SetBackgroundColour('red')
                    self.ch_status[ch][INDEX_EC].Refresh()
                    self.ch_status[ch][INDEX_LR].SetValue('fail')
                else:
                    self.ch_status[ch][INDEX_LR].SetValue('pass')

                self.ch_status[ch][INDEX_LC].SetValue(bstr[2])




if __name__ == '__main__':
    app = MyApp(True, filename='debug')
    #app = MyApp(False)
    app.MainLoop()




































