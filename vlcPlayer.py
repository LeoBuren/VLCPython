import vlc
import wx
import win32con
import os

import settings
from os.path import basename, isfile


class TimeDataStruct:
    def __init__(self, start, end):
        if start == end or start < 0 or end < 0:
            Exception('Error creating TimeData Object')
        if start > end:
            self.start = end
            self.end = start
        else:
            self.start = start
            self.end = end


class VideoStruct:
    def __init__(self, name, directory=settings.INPUT_FOLDER):
        self.name = name
        self.timeArray = []
        self.path = os.path.join(settings.INPUT_FOLDER, name)

    def append(self, obj):
        return self.timeArray.append(obj)

    def pop(self):
        return self.timeArray.pop()

    def get(self):
        return self.timeArray

    def toString(self):
        return f'name: {self.name}, count: {len(self.timeArray)}'

    def setPath(self, directory):
        self.path = os.path.join(directory, self.name)


class Player(wx.Frame):
    def __init__(self, title='', videos=[], downFunc=any, nextFunc=any):
        wx.Frame.__init__(self, None, -1, title=title or 'wxVLC',
                          pos=wx.DefaultPosition, size=(int(1920/1.5), int(1080/1.5)))

        self.downFunc = downFunc
        self.nextFunc = nextFunc
        self.videos = videos

        try:
            self._getVideo()
        except:
            raise
        self.storedTime = -1

        self._UI()

        # VLC player controls
        self.Instance = vlc.Instance('-q')
        self.player = self.Instance.media_player_new()

        self.OnOpen(None)

    def _UI(self):
        self.f1HotKeyId = 0x0001
        self.f2HotKeyId = 0x0002
        self.f3HotKeyId = 0x0003
        self.RegisterHotKey(self.f1HotKeyId, win32con.NULL, win32con.VK_F1)
        self.RegisterHotKey(self.f2HotKeyId, win32con.NULL, win32con.VK_F2)
        self.RegisterHotKey(self.f3HotKeyId, win32con.NULL, win32con.VK_F3)

        # Menu Bar
        #   File Menu
        self.frame_menubar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.file_menu.Append(1, "&Open...", "Open from file...")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(2, "&Close", "Quit")
        self.Bind(wx.EVT_MENU, self.OnOpen, id=1)
        self.Bind(wx.EVT_MENU, self.OnExit, id=2)
        self.frame_menubar.Append(self.file_menu, "File")
        self.SetMenuBar(self.frame_menubar)

        # Panels
        # The first panel holds the video and it's all black
        self.videopanel = wx.Panel(self, -1)
        self.videopanel.SetBackgroundColour(wx.BLACK)

        # The second panel holds controls
        self.ctrlpanel = wx.Panel(self, -1)
        self.timeslider = wx.Slider(self.ctrlpanel, -1, 0, 0, 1000)
        self.timeslider.SetRange(0, 1000)
        self.pause = wx.Button(self.ctrlpanel, label="Pause")
        self.pause.Disable()
        self.play = wx.Button(self.ctrlpanel, label="Play")
        self.stop = wx.Button(self.ctrlpanel, label="Stop")
        self.stop.Disable()
        self.mute = wx.Button(self.ctrlpanel, label="Mute")
        self.volslider = wx.Slider(
            self.ctrlpanel, -1, 0, 0, 100, size=(100, -1))

        # Bind controls to events
        self.Bind(wx.EVT_BUTTON, self.OnPlay,   self.play)
        self.Bind(wx.EVT_BUTTON, self.OnPause,  self.pause)
        self.Bind(wx.EVT_BUTTON, self.OnStop,   self.stop)
        self.Bind(wx.EVT_BUTTON, self.OnMute,   self.mute)
        self.Bind(wx.EVT_SLIDER, self.OnSearch, self.timeslider)
        self.Bind(wx.EVT_SLIDER, self.OnVolume, self.volslider)
        self.Bind(wx.EVT_HOTKEY, self.HandleHotKey)

        # Give a pretty layout to the controls
        ctrlbox = wx.BoxSizer(wx.VERTICAL)
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        # box1 contains the timeslider
        box1.Add(self.timeslider, 1)
        # box2 contains some buttons and the volume controls
        box2.Add(self.play, flag=wx.RIGHT, border=5)
        box2.Add(self.pause)
        box2.Add(self.stop)
        box2.Add((-1, -1), 1)
        box2.Add(self.mute)
        box2.Add(self.volslider, flag=wx.TOP | wx.LEFT, border=5)
        # Merge box1 and box2 to the ctrlsizer
        ctrlbox.Add(box1, flag=wx.EXPAND | wx.BOTTOM, border=10)
        ctrlbox.Add(box2, 1, wx.EXPAND)
        self.ctrlpanel.SetSizer(ctrlbox)
        # Put everything togheter
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.videopanel, 1, flag=wx.EXPAND)
        sizer.Add(self.ctrlpanel, flag=wx.EXPAND |
                  wx.BOTTOM | wx.TOP, border=10)
        self.SetSizer(sizer)
        self.SetMinSize((350, 300))

        # finally create the timer, which updates the timeslider
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

    def _getVideo(self):
        if not len(self.videos):
            self.downFunc()
            Exception('Ran out of videos')

        self.video = VideoStruct(self.videos.pop())
        print(f'Editing {self.video.name}, {len(self.videos)} left.')

    def HandleHotKey(self, evt):
        time = self.player.get_time()
        if time == -1:
            return

        match evt.Id:
            case self.f1HotKeyId:
                if self.storedTime == -1:
                    self.storedTime = time
                else:
                    self.video.append(TimeDataStruct(self.storedTime, time))
                    self.storedTime = -1
            case self.f2HotKeyId:
                if self.storedTime != -1:
                    self.storedTime = -1
                else:
                    try:
                        self.video.pop()
                    except:
                        pass
            case self.f3HotKeyId:
                self.nextFunc(self.video)
                try:
                    self._getVideo()
                except:
                    return

                self.OnOpen(None)

        self.HandlePaint()

    def Exit(self):
        self.player.stop()
        self.player.release()
        self.Instance.release()
        self.Close()

    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()

    def OnOpen(self, evt):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """

        if isfile(self.video.path):  # Creation
            self.Media = self.Instance.media_new(str(self.video.path))
            self.player.set_media(self.Media)
            # Report the title of the file chosen
            title = self.player.get_title()
            # if an error was encountred while retrieving the title,
            # otherwise use filename
            self.SetTitle("%s - %s" %
                          (title if title != -1 else 'wxVLC', basename(self.video.name)))

            # set the window id where to render VLC's video output
            handle = self.videopanel.GetHandle()
            self.player.set_hwnd(handle)

            self.volslider.SetValue(int(self.player.audio_get_volume() / 2))
            self.OnPlay(None)

    def TimeSliderValueToXCoord(self, value):
        ratio = value / self.timeslider.GetMax()

        if ratio < 0.5:
            return int(ratio*self.ctrlpanel.GetSize()[0])+int(12*(1-ratio))

        return int(ratio*self.ctrlpanel.GetSize()
                   [0])-int(12*(1-(ratio-0.5)))

    def HandlePaint(self):
        dc = wx.ClientDC(self.ctrlpanel)
        dc.Clear()

        dc.SetBrush(wx.Brush(wx.GREEN))
        for box in self.video.get():
            x = self.TimeSliderValueToXCoord(
                box.start)
            width = self.TimeSliderValueToXCoord(
                box.end) - x
            dc.DrawRectangle(x, 0,
                             width, 36)

        dc.SetBrush(wx.Brush(wx.RED))
        if self.storedTime != -1:
            dc.DrawRectangle(self.TimeSliderValueToXCoord(
                self.timeslider.GetValue()), 0, 2, 42)

    def OnPlay(self, evt):
        """Toggle the status to Play/Pause.

        If no file is loaded, open the dialog window.
        """
        # check if there is a file to play, otherwise open a
        # wx.FileDialog to select a file
        if not self.player.get_media():
            self.OnOpen(None)
            # Try to launch the media, if this fails display an error message
        elif self.player.play():  # == -1:
            self.errorDialog("Unable to play.")
        else:
            # adjust window to video aspect ratio
            # w, h = self.player.video_get_size()
            # if h > 0 and w > 0:  # often (0, 0)
            #     self.videopanel....
            self.timer.Start(1000)  # XXX millisecs
            self.play.Disable()
            self.pause.Enable()
            self.stop.Enable()

    def OnPause(self, evt):
        """Pause the player.
        """
        if self.player.is_playing():
            self.play.Enable()
            self.pause.Disable()
        else:
            self.play.Disable()
            self.pause.Enable()
        self.player.pause()

    def OnStop(self, evt):
        """Stop the player.
        """
        self.player.stop()
        # reset the time slider
        self.timeslider.SetValue(0)
        self.timer.Stop()
        self.play.Enable()
        self.pause.Disable()
        self.stop.Disable()

    def OnTimer(self, evt):
        """Update the time slider according to the current movie time.
        """
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        try:
            length = self.player.get_length()
        except:
            self.Close()
            return

        self.timeslider.SetRange(-1, length)

        # update the time on the slider
        time = self.player.get_time()
        self.timeslider.SetValue(time)

    def OnMute(self, evt):
        """Mute/Unmute according to the audio button.
        """
        muted = self.player.audio_get_mute()
        self.player.audio_set_mute(not muted)
        self.mute.SetLabel("Mute" if muted else "Unmute")
        # update the volume slider;
        # since vlc volume range is in [0, 200],
        # and our volume slider has range [0, 100], just divide by 2.
        # self.volslider.SetValue(self.player.audio_get_volume() / 2)

    def OnSearch(self, evt):
        self.player.set_time(
            min(self.player.get_length(), self.timeslider.GetValue()))

    def OnVolume(self, evt):
        """Set the volume according to the volume sider.
        """
        volume = self.volslider.GetValue() * 2
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def errorDialog(self, errormessage):
        """Display a simple error dialog.
        """
        edialog = wx.MessageDialog(self, errormessage, 'Error', wx.OK |
                                   wx.ICON_ERROR)
        edialog.ShowModal()
