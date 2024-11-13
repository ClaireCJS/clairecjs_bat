VLC_LUA_PORT = "8080"
VLC_PASSWORD = 'password'









import requests
import logging as logging
for handler in logging.root.handlers[:]: logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.WARNING,
    format='\t\t[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.WARNING)
logger.debug("clairecjs_vlc started")


def get_vlc_status():
    vlc_lua_port   = VLC_LUA_PORT
    vlc_password   = VLC_PASSWORD
    vlc_ip_address = "localhost"
    url = f"http://{vlc_ip_address}:{vlc_lua_port}/requests/status.json"
    logger.debug(f"* VLC control URL is {url}")

    # If you set a password, use HTTP Basic Authentication
    auth = ('', vlc_password)  # (username, password), leave username as an empty string

    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        # The response will contain JSON data with the status of VLC
        status = response.json()
        #print(status)

        # Extracting specific values
        show_name        = status.get(    'info', {}).get(   'title', 'Unknown')
        video_resolution = status.get(   'video', {}).get(   'width', 'Unknown'), status.get('video', {}).get('height', 'Unknown')
        frame_rate       = status.get(   'video', {}).get(     'fps', 'Unknown')
        codec            = status.get(    'info', {}).get(   'codec', 'Unknown')
        language         = status.get(    'info', {}).get('language', 'Unknown')
        position         = status.get('position', 'Unknown')

        #print(f"Show Name: {show_name}")
        #print(f"Video Resolution: {video_resolution[0]}x{video_resolution[1]}")
        #print(f"Frame Rate: {frame_rate} fps")
        #print(f"Codec: {codec}")
        #print(f"Language: {language}")
        #print(f"Position: {position}")

        return status
    else:
        print(f"Failed to connect to VLC. Status code: {response.status_code}")
        return None

def is_vlc_running():
    """Check if VLC is running by checking for VLC's process."""
    # This approach will vary depending on the OS. Here's a simple cross-platform example:
    import psutil
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'vlc.exe' or proc.info['name'] == 'vlc':
            return True
    return False

if __name__ == "__main__":
    print(f"\n******* is_vlc_running ************")
    print(f"--> {is_vlc_running()}")

    print(f"\n******* getting vlc_status *******")
    vlc_status = get_vlc_status()
    #rint(f"--> {get_vlc_status}")
    print(f"\n--> vlc status:\n")
    for key, value in vlc_status.items():
        print(f"    {key}: {value}")
    print(f"\n\n--> vlc status:\n")
    for key, value in vlc_status.items(): print(f"\t{key}\t:\t{value}")

    print(f"\n\n\n******* vlc information? *******")
    for key, value in vlc_status.get("information").items(): print(f"\t{key}\t:\t{value}")



    print(f"\n\n\n******* vlc category info? *******")
    information = vlc_status .get("information", {"Unknown"})
    category    = information.get(   "category", {"Unknown"})
    for key, value in category.items(): print(f"\t{key}\t:\t{value}")



    print(f"\n\n\n******* vlc meta  info? *******")
    information = vlc_status .get("information", {"Unknown"})
    category    = information.get(   "category", {"Unknown"})
    meta        = category   .get(       "meta", {"Unknown"})
    for key, value in meta.items(): print(f"\t{key}\t:\t{value}")

    print(f"\n\n\n******* vlc specific info? *******")
    vlc_status      = get_vlc_status()
    vlc_information = vlc_status     .get("information", {"Unknown"           })
    vlc_category    = vlc_information.get(   "category", {"Unknown"           })
    vlc_meta        = vlc_category   .get(       "meta", {"Unknown"           })

    print(f"\n\n\n******* vlc title? *******")
    vlc_title       = vlc_meta       .get(      "title", {meta.get("filename")})
    print(f"\t\tvlc title: {vlc_title}")


    print(f"\n\n\n******* vlc nice info? *******")
    vlc_status        = get_vlc_status()
    vlc_information   = vlc_status     .get(  "information", {"Unknown"           })
    vlc_length_in_s   = vlc_status     .get(       "length", {"Unknown"           })
    vlc_position_in_s = vlc_status     .get(         "time", {"Unknown"           })
    vlc_category      = vlc_information.get(     "category", {"Unknown"           })
    vlc_meta          = vlc_category   .get(         "meta", {"Unknown"           })
    vlc_title         = vlc_meta       .get(        "title", {"Unknown"           })  #fall back on filename?
    vlc_season        = vlc_meta       .get( "seasonNumber", {"Unknown"           })
    vlc_episode       = vlc_meta       .get("episodeNumber", {"Unknown"           })
    vlc_filename      = vlc_meta       .get(     "filename", {"Unknown"           })
    print(f"\t\tvlc    title: {vlc_title      }")
    print(f"\t\tvlc   season: {vlc_season     }")
    print(f"\t\tvlc       ep: {vlc_episode    }")
    print(f"\t\tvlc filename: {vlc_filename   }")
    print(f"\t\tvlc  len (s): {vlc_length_in_s}")



































































#### TRASHCAN:

#def fetch_vlc_metadata():
#    """Fetch metadata from VLC using python-vlc."""
#    import vlc
#    if is_vlc_running():
#        try:
#            instance = vlc.Instance()                        # Initialize VLC instance
#            player   = vlc.MediaPlayer(instance)
#            media    = player.get_media()                    # Get media
#            if media:                                        # Fetch and print the current media title
#                title = media.get_mrl()                      # This may return the file path or URL
#                dashboard_logger.debug("Current VLC Title (Python VLC):", title)
#                for key in ["title", "artist", "album", "genre", "tracknumber", "date", "comment"]:
#                    value = media.get_meta(getattr(vlc.MediaMeta, f'META_{key.upper()}', None))
#                    dashboard_logger.debug(f"  {key}: {value}")
#                duration = media.get_duration()
#                state = player.get_state()
#                for key in dir(media):                       # Get other details if available
#                    if key.startswith("get_"):
#                        try:
#                            value = getattr(media, key)()
#                            if value: dashboard_logger.debug(f"  {key}: {value}")
#                        except Exception as e:
#                            pass
#                dashboard_logger.debug("All info (mrl):", mrl)
#            else:
#                dashboard_logger.debug("No media is currently loaded in VLC.")
#            return media;
#        except Exception as e:
#            dashboard_logger.debug(f"Error with VLC Python bindings: {e}")
#    else:
#        dashboard_logger.debug("VLC is not running.")
#    return None

