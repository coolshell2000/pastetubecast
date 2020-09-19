import time, datetime
import threading
import subprocess
import sys
import pyperclip
import curses

import termios, fcntl, os

# ls | mpv --playlist=-
playlist = []
playlist_done = []  # key is pid of the mpv
playlist_current_item = ""
status_playing = False

def update_playlist(title, playlist, info_status="info"):
    curses.initscr()

    height = len(playlist) + 30
    win = curses.newwin(height + 7, 80, 0, 0)  # (height, width, begin_y, begin_x)
    win.border(0)
    win.addstr(0, 1, title)
    for index, item in enumerate(playlist):
        win.addstr(index + 1, 1, item)
        win.refresh()
    #win.addstr(len(playlist) + 4, 4, info_status)
    win.addstr(len(playlist) + 30, 4, info_status)
    win.refresh()


def is_mpv_stopped(process_mpv):
    update_playlist(title="in poll return true always playing now. mpv pid:{}".format(process_mpv.pid),
                    playlist=playlist,
                    info_status=str(datetime.datetime.now())
                    )
    sys.exit(0)
    return True
    #
    # poll = process_mpv.poll()
    # if poll == None: #still runningupdate_playlist(title="poll.. playing now. mpv pid:{}".format(process_mpv.pid), playlist=playlist)
    #     update_playlist(title="poll.. playing now. mpv pid:{}".format(process_mpv.pid), playlist=playlist)
    #     return False
    # else:
    #     update_playlist(title="poll.. ready to load next for playing...", playlist=playlist)
    #     return True

def is_url_youtube_watch(url):
    global playlist
    if url.startswith("https://www.youtube.com/watch") and url not in playlist and url not in playlist_done:
        return True
    return False

def push2queue(clipboard_content):
    global playlist

    playlist = load_playlist()
    
    str_youtube_watch_url = str(clipboard_content)
    playlist.insert(0, str_youtube_watch_url)
    msg = "append youtube url at " + str(datetime.datetime.now())

    save_playlist(playlist)
    # path_playlist_file = "playlist.txt"
    # with open(path_playlist_file, "w") as fp:
    #      fp.writelines("%s\n" % item for item in playlist)
    #
    update_playlist(title=msg, playlist=playlist)
    # #subprocess.run(["/mnt/nfs/nethome/bt/youtube_cast.bash", "pi", "192.168.0.18", str_youtube_watch_url])
    # if len(sys.argv)==2:
    #     subprocess.run(["/mnt/nfs/nethome/bt/youtube_cast.bash", "pi", sys.argv[1], str_youtube_watch_url])
    # else:
    #     subprocess.run(["/mnt/nfs/nethome/bt/youtube_cast.bash", "pi", "192.168.0.18", str_youtube_watch_url])

def save_playlist(playlist):
    path_playlist_file = "playlist.txt"
    with open(path_playlist_file, "w") as fp:
         fp.writelines("%s\n" % item for item in playlist)

def load_playlist():
    playlist=[]
    path_playlist_file="playlist.txt"
    if path.exists(path_playlist_file):
        with open(path_playlist_file, "r") as fp:
            playlist = list(line for line in (l.strip() for l in fp) if line)  # Non-blank lines
            # playlist = fp.readlines()
            print ("ok loaded {} items from playlist file {}".format(len(playlist), path_playlist_file))
            print("playlist:{}".format(playlist))
    return playlist


def mpv_play(mode="l"):
    global playlist
    if len(playlist) > 0 and status_playing == False:
        if mode == "l":
            playlist_current_item = playlist.pop(-1)
        else:
            playlist_current_item = playlist.pop(0)
        save_playlist(playlist)

        process_mpv = subprocess.Popen(["/mnt/nfs/nethome/bt/youtube_cast.bash", "pi", "p41", playlist_current_item, "--fullscreen --screen=1"], stdout=subprocess.PIPE, shell=False)
        #process_mpv = subprocess.Popen(["/mnt/nfs/nethome/bt/youtube_cast.bash", "pi", "p41", playlist_current_item], stdout=subprocess.PIPE, shell=False)
        output, err = process_mpv.communicate()
        playlist_done.append(playlist_current_item)

        update_playlist(
            title="   poll.. playing.. pid:{} {}".format(process_mpv.pid, playlist_current_item.split("watch?v=")[-1]),
            playlist=playlist,
            info_status=output)
    else:
        update_playlist(title="playing or empty playlist! pls wait or add more through url copy", playlist=playlist)




class ClipboardWatcher(threading.Thread):
    def __init__(self, predicate, callback, pause=5.):
        super(ClipboardWatcher, self).__init__()
        self._predicate = predicate
        self._callback = callback
        self._pause = pause
        self._stopping = False

        global playlist


    def run(self):
        recent_value = ""
        while not self._stopping:
            tmp_value = pyperclip.paste()
            if tmp_value != recent_value:
                recent_value = tmp_value
                if self._predicate(recent_value):
                    self._callback(recent_value)
            time.sleep(self._pause)

    def stop(self):
        self._stopping = True


class Mpvfeeder(threading.Thread):
    def __init__(self, predicate, callback, pause=5.):
        super(Mpvfeeder, self).__init__()
        self._predicate = predicate
        self._callback = callback
        self._pause = pause
        #self._flag = True # set to True to allow thread to run as non blocking
        self._stopping = False
        self.process_mpv = None

        #global playlist

    def run(self):
        recent_value = ""
        while not self._stopping:
            if self.process_mpv is None:
                if len(playlist) > 0:
                    self._callback(playlist[0])
            time.sleep(self._pause)


    def stop(self):
        self._stopping = True

    def next(self):
        while not self._stopping:
            if len(playlist) > 0:
                self._callback(playlist[0])
            time.sleep(self._pause)



import os.path
from os import path

def main():
    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    watcher = ClipboardWatcher(is_url_youtube_watch,
                               push2queue,
                               1.)
    watcher.start()

    print("\nthread ClipboardWatcher started.. Waiting clipboard to queue...")
    time.sleep(1)
    mpv = Mpvfeeder(is_mpv_stopped, mpv_play, 1.)
    mpv.start()
    print("\nthread Mpvfeeder started.. Waiting to play from queue...")

    global playlist

    playlist = load_playlist()


    curses.initscr()



    try:
        count = 0
        while 1:
            time.sleep(0.2)
            count = count + 1
            #print(".")
            try:
                try:
                    c = sys.stdin.read(1)
                    if c:
                        curses.initscr()
                        if len(playlist_done) > 0:
                            msg = playlist_done[-1]
                        else:
                            msg = "extra info"
                        char_key_pressed = repr(c)
                        update_playlist(title="key detected - {} - (l)ast/(n)ext/(c)ast/(q)uit - {}"
                                        .format(char_key_pressed, playlist_current_item.split("watch?v=")[-1]),
                                        playlist=playlist,
                                        info_status=msg)
                        ### to make another threadClass for key action handling
                        # if c == "p":
                        #     mpv.pause() #mpv_play(mode=char_key_pressed)
                        # if c == "c":
                        #     mpv.resume()
                        # if c == "n":
                        #     print ("ns")
                        #     #mpv.next()
                        #### to pass on key event to mpv
                except IOError:
                    pass
            except KeyboardInterrupt:
                watcher.stop()
                curses.endwin()
                break

    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)


if __name__ == "__main__":
    main()