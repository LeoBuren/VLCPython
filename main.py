from vlcPlayer import Player
import os
import wx
from subprocess import call
import queue
import time
import threading

import settings


def construct_input_file_str(file, start, end):
    input_file_str = '-ss ' + str(int(start/1000)) + ' '
    input_file_str += '-i "' + file + '" '
    input_file_str += '-t ' + str(int(end/1000)) + ' '

    return input_file_str


def join_folder(files, folder, video):
    print('joining all .ts files')

    execStr = settings.FFMPEG + ' -i "concat:'
    for file in files[:-1]:
        execStr += file+'|'
    execStr += files[-1]
    execStr += '" -c copy -bsf:a aac_adtstoasc edited_'+video+'.mp4'

    call(execStr, cwd=folder)

    os.replace(os.path.join(settings.OUTPUT_FOLDER, 'edited_'+video+'.mp4'),
               os.path.join(settings.BASE_FOLDER, 'edited_'+video+'.mp4'))

    for file in files:
        os.remove(os.path.join(settings.OUTPUT_FOLDER, file))


class Worker(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
        self.isRunning = True
        self.isFinished = False

    def _BuildFilterString(self, objs):
        res = '\''
        for i, obj in enumerate(objs):
            if i != 0:
                res += '+'
            _s = str(int(obj.start/1000))
            _e = str(int(obj.end/1000))
            res += f"between(t, {_s}, {_e})"

        return res + '\''

    def Slice(self, name, objs):
        filterString = self._BuildFilterString(objs)

        if settings.SCALE_FACTOR == 1:
            fc = f'-filter_complex "[:v]select={filterString}, setpts=N/FRAME_RATE/TB[v];[:a]aselect={filterString}, asetpts=N/SR/TB[a]"'
        else:
            fc = f'-filter_complex "[:v]select={filterString}, setpts=N/FRAME_RATE/TB, scale={int(1920*settings.SCALE_FACTOR)}:{int(1080*settings.SCALE_FACTOR)}, crop={settings.W}:{settings.H}[v];[:a]aselect={filterString}, asetpts=N/SR/TB[a]"'

        call(
            f'{settings.FFMPEG} -i "{name}" {fc} -map "[v]" -map "[a]" {settings.OUTPUT_SETTINGS} "{name}_edited.mp4"', cwd=settings.INPUT_FOLDER)

        os.replace(os.path.join(settings.INPUT_FOLDER, name+'_edited.mp4'),
                   os.path.join(settings.OUTPUT_FOLDER, name+'_edited.mp4'))

    def run(self):
        while self.isRunning or not self.q.empty():
            video = self.q.get()
            print('Editing ', video.toString()+',', str(
                self.q.qsize()), 'left in queue')

            if not len(video.get()):
                continue

            self.Slice(video.name, video.get())

            os.replace(video.path,
                       os.path.join(settings.BASE_FOLDER, video.name))

            print('finished with', video.name)

        self.isFinished = True

    def Down(self):
        self.isRunning = False


class ThreadedEditorController:
    def __init__(self):
        self.objs = queue.Queue()
        self.worker = Worker(self.objs)
        threading.Thread(target=self.worker.run, daemon=True).start()

    def Put(self, obj):
        print('adding ', obj.toString(), 'to queue')
        return self.objs.put(obj)

    def Down(self):
        self.worker.Down()
        while not self.worker.isFinished:
            time.sleep(1)


class VideoEditorController:
    def __init__(self, videos, nextFunc, downFunc):
        self.app = wx.App()
        self.videos = videos
        self.downFunc = downFunc
        self.player = Player(
            videos=videos, downFunc=self.Down, nextFunc=nextFunc)

        self.Run()

    def Run(self):
        print('starting editor')

        self.player.Centre()
        self.player.Show()
        # run the application
        self.app.MainLoop()

    def Down(self):
        print('closing editor')
        self.player.Hide()
        self.player.Exit()
        self.app.ExitMainLoop()
        self.player.Destroy()
        self.downFunc()


if __name__ == "__main__":
    if not os.path.exists(settings.INPUT_FOLDER):
        raise Exception('Missing subfolder')

    files = next(os.walk(settings.INPUT_FOLDER), (None, None, []))[2]

    editorController = ThreadedEditorController()
    videoController = VideoEditorController(
        files, editorController.Put, editorController.Down)
