import xbmc
import xbmcgui
import json
import urllib.request
import time
import threading
import os

# =========================
# NOTIFICA INIZIALE
# =========================
xbmcgui.Dialog().notification(
    "Kodi Discord RPC",
    "Connected Via Proxy",
    xbmcgui.NOTIFICATION_INFO,
    3000
)

# =========================
# CONFIG
# =========================

SERVER_URL = "http://127.0.0.1:5678/status"
POLL_INTERVAL = 2
WATCHDOG_INTERVAL = 15

monitor = xbmc.Monitor()
last_window_id = None
send_lock = threading.Lock()
last_send_time = 0

# =========================
# PLAYER EVENTS
# =========================
class PlayerEvents(xbmc.Player):
    def onAVStarted(self):
        send(get_activity(force=True))

    def onPlayBackPaused(self):
        send(get_activity(force=True))

    def onPlayBackResumed(self):
        send(get_activity(force=True))

    def onPlayBackStopped(self):
        send(get_activity(force=True))

    def onPlayBackEnded(self):
        send(get_activity(force=True))

player_events = PlayerEvents()

# =========================
# PLAYBACK INFO
# =========================
def get_playback():
    player = xbmc.Player()

    if not player.isPlaying():
        return None

    filename = os.path.basename(player.getPlayingFile() or "")

    # VIDEO
    if player.isPlayingVideo():
        info = player.getVideoInfoTag()
        buttons = [
            {"label": "IMDb", "url": f"https://www.imdb.com/find?q={filename}"},
            {"label": "TMDB", "url": f"https://www.themoviedb.org/search?query={filename}"}
        ]

        return {
            "type": "video",
            "title": info.getTitle() or filename or "Unknown video",
            "show": info.getTVShowTitle(),
            "season": info.getSeason(),
            "episode": info.getEpisode(),
            "duration": int(player.getTotalTime()),
            "position": int(player.getTime()),
            "paused": player.isPaused(),
            "large_image": "kodi_video",
            "large_text": filename or info.getTitle(),
            "small_image": "pause" if player.isPaused() else "play",
            "details": filename or info.getTitle(),
            "buttons": buttons[:2]
        }

    # MUSIC
    if player.isPlayingAudio():
        info = player.getMusicInfoTag()
        artist = " - ".join(info.getArtist()) if info.getArtist() else "Unknown artist"
        buttons = [
            {"label": "Artist on Google", "url": f"https://www.google.com/search?q={artist}"}
        ]

        return {
            "type": "music",
            "title": info.getTitle() or filename or "Unknown track",
            "artist": artist,
            "album": info.getAlbum() or "",
            "duration": int(player.getTotalTime()),
            "position": int(player.getTime()),
            "paused": player.isPaused(),
            "large_image": "music",
            "large_text": filename or info.getTitle(),
            "small_image": "pause" if player.isPaused() else "play",
            "details": filename or info.getTitle(),
            "buttons": buttons
        }

    return None

# =========================
# MENU INFO
# =========================
def get_menu():
    global last_window_id

    label = xbmc.getInfoLabel("System.CurrentWindow") or "Kodi menu"
    window_id = xbmc.getInfoLabel("System.CurrentWindowId") or "0"

    changed = window_id != last_window_id
    last_window_id = window_id

    window_map = {
        "10000": ("images", "Browsing images"),
        "10025": ("tvshows", "Browsing TV shows"),
        "home": ("kodi", "Kodi home")
    }

    large_image, large_text = window_map.get(window_id, ("kodi_menu", label))

    return {
        "type": "menu",
        "details": label,
        "large_image": large_image,
        "large_text": large_text,
        "force": changed
    }

# =========================
# ACTIVITY WRAPPER
# =========================
def get_activity(force=False):
    data = get_playback() or get_menu()
    if not data:
        return None
    if force:
        data["force"] = True
    return data

# =========================
# HTTP SEND (SANITIZED)
# =========================
def send(data):
    global last_send_time

    if not data:
        return

    with send_lock:
        now = time.time()
        if not data.get("force", False) and now - last_send_time < POLL_INTERVAL:
            return

        try:
            clean_data = {}
            for k, v in data.items():
                if v is None:
                    continue
                if k == "buttons" and (not v or len(v) == 0):
                    continue
                clean_data[k] = v

            req = urllib.request.Request(
                SERVER_URL,
                data=json.dumps(clean_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=2):
                pass

            last_send_time = now

        except Exception as e:
            xbmc.log("[RPC SEND ERROR] {}".format(str(e)), xbmc.LOGERROR)

# =========================
# BACKGROUND THREAD
# =========================
def activity_loop():
    while not monitor.abortRequested():
        try:
            activity = get_activity()
            if activity:
                if time.time() - last_send_time > WATCHDOG_INTERVAL:
                    activity["force"] = True
                send(activity)
        except Exception as e:
            xbmc.log(
                "[RPC LOOP ERROR] {}".format(str(e)),
                xbmc.LOGERROR
            )
        time.sleep(POLL_INTERVAL)

threading.Thread(target=activity_loop, daemon=True).start()

while not monitor.abortRequested():
    time.sleep(1)
