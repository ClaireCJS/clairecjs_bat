"""
MIT License

Copyright (c) 2018 Niko Mätäsaho
Copyright (c) 2001-2006 Shalabh Chaturvedi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# This is a modification of WinampRPC's winamp.py found at https://github.com/Visperi/WinampRPC
import time

# Import only the modules for LCD communication
import sys
import os
# Trying to borrow from the official library, but I had to steal some of it for my stuff, and it was a strange compromise:
library_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'turing_smart_screen-python')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'turing_smart_screen-python', 'library')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'turing_smart_screen-python', 'res')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'turing_smart_screen-python', 'res', 'backgrounds')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'turing_smart_screen-python', 'res', 'fonts')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'turing_smart_screen-python', 'res', 'icons')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'turing_smart_screen-python', 'res', 'themes'))
]
for path in library_paths: sys.path.append(path)                    # Append all paths to sys.path
#print(f"sys.path.append({library_paths})")
from library.lcd.lcd_comm_rev_a import LcdCommRevA, Orientation
from library.lcd.lcd_comm_rev_b import LcdCommRevB
from library.lcd.lcd_comm_rev_c import LcdCommRevC
from library.lcd.lcd_comm_rev_d import LcdCommRevD
from library.lcd.lcd_simulated  import LcdSimulated


############################################## LOGGING: ##############################################
import logging as logging
for    handler in logging.root.handlers[:]: logging.root.removeHandler(handler)
logging.basicConfig(level=logging.DEBUG,format='\t\t[%(levelname)s] %(message)s')
logger                  = logging.getLogger(__name__)
logger.setLevel          (logging.WARNING)
logger.debug             ("dashboard logger started")
############################################## LOGGING ###############################################

import tempfile
import glob
from pathlib import Path

#global previous_track_title
#global cleared
#global trackinfo_raw
#global artist
#global title
global w
#global custom_assets
#global winamp_version
#global trackinfo_raw

previous_track_title = ""
trackinfo_raw  = ""


from enum import Enum
from typing import (Tuple, Union, Optional, List)



def test_examples():
    # Example trackinfo_raw strings
    examples = [
        "The Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "hangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "rs - Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "e Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        " - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "namp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "*** 4809. The Coathangers – Excuse Me? - Winamp ***",
        "9. The Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "e Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "thangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "ers - Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        " Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "se Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "inamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "p *** 4809. The Coathangers – Excuse Me? - Winamp",
        "809. The Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "The Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "oathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "ngers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        " - Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "cuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        " Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "mp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "4809. The Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        " The Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "Coathangers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "angers – Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "s - Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "Excuse Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "e Me? - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        " - Winamp *** 4809. The Coathangers – Excuse Me? - Winamp",
        "namp *** 4809. The Coathangers – Excuse Me? - Winamp",
        #---------------------------------------------------------------
        "PURPOSEFUL ERROR",
        "Winamp *** 30. The Sword – Freya - Winamp",
        " *** 76. Fugazi – Suggestion - Winamp ***",
        " *** 127. Arthur Bradford – Roslyn's Dog - Winamp ***",
        "amp *** 139. The Dreadnoughts – Black Sea Gale - Winamp",
        "inamp *** 141. Pixies – Bel Esprit - Winamp",
        "Winamp *** 143. The Dreadnoughts – Black Letters - Winamp",
        "3) - Winamp *** 164. They Might Be Giants – Hide Away Folk Family (live) (2013) - Winamp",
    ]

    for example in examples:
        band_name, title = extract_band_and_track_from_raw_title(example)
        print(f"Input: {example}")
        print(f"Band Name: {band_name}\nTrack Name: {title}\n")


import win32api
import win32gui

WM_COMMAND = 0x0111
"""
First slot for menu control messages in Windows API.
"""
WM_USER = 0x400
"""
First slot for user defined messages in Windows API.
"""


class MenuCommand(Enum):
    """
    Enum representing WM_COMMAND commands with correct data values. These commands are identical to pressing menus
    and buttons in the player GUI.
    """

    ToggleRepeat = 40022
    """
    Toggle track repeating.
    """
    ToggleShuffle = 40023
    """
    Toggle track shuffling.
    """
    PreviousTrack = 40044
    """
    Go to previous track.
    """
    Play = 40045
    """
    Play current track or start it over if already playing.
    """
    TogglePause = 40046
    """
    Toggle pause.
    """
    Stop = 40047
    """
    Stop the current track. Seeks the track position to zero position.
    """
    NextTrack = 40048
    """
    Go to next track.
    """
    RaiseVolume = 40058
    """
    Raise volume by 1%.
    """
    LowerVolume = 40059
    """
    Lower volume by 1%.
    """
    FastRewind = 40144
    """
    Rewind the current track by 5 seconds.
    """
    FadeOutAndStop = 40147
    """
    Fade out and stop after the track.
    """
    FastForward = 40148
    """
    Fast forward the current track by 5 seconds.
    """
    StopAfterTrack = 40157
    """
    Stop after the current track.
    """


class UserCommand(Enum):
    """
    Enum representing WM_USER user commands sent to Winamp. These commands are sent programmatically to Winamp API and
    are not strictly equal to pressing buttons in player GUI. Setter commands often need a separate value 'data' to
    have effect.
    """

    WinampVersion = 0
    """
    Current Winamp version in hexadecimal number.
    """
    PlayingStatus = 104
    """
    Current playing status. Returns 1 for playing, 3 for paused and otherwise stopped.
    """
    TrackStatus = 105
    """
    Get current tracks' status. Track position in milliseconds if data is set to 0, or track length in seconds if
    data is 1.
    """
    SeekTrack = 106
    """
    Seek current track to position in milliseconds specified in data.
    """
    DumpPlaylist = 120
    """
    Dump current playlist to WINAMPDIR/winamp.m3u and resepective .m3u8 files, and return the current playlist
    position.
    """
    ChangeTrack = 121
    """
    Set the playlist position to position defined in data.
    """
    SetVolume = 122
    """
    Set the playback volume to value specified in data. The range is between 0 (muted) and 255 (max volume).
    """
    PlaylistLength = 124
    """
    Get the current playlist length in number of tracks.
    """
    PlaylistPosition = 125
    """
    Get the current playlist position in tracks.
    """
    TrackInfo = 126
    """
    Get technical information about the current track. Data values give following results: 0 for samplerate, 1 for
    bitrate and 2 for number of channels.
    """


class PlayingStatus(Enum):
    """
    Enum representing the current playing status of Winamp player.
    """

    Stopped = 0
    """
    The player is stopped or not running. Although this enum value has value of zero, the status in Winamp is
    'otherwise' returned as stopped if it does not match playing status or paused status.
    """
    Playing = 1
    """
    A track is currently playing.
    """
    Paused = 3
    """
    Current track is paused.
    """


class Track:
    """
    A class representing a track.
    """

    def __init__(self, title: str, sample_rate: int, bitrate: int, channels: int, length: int):
        """
        :param title: The track title in Winamp window. Usually in format {track_num}. {artist} - {track_name} - Winamp
        :param sample_rate: The track sample rate
        :param bitrate: The track bitrate
        :param channels: Number of channels in the track
        :param length: The track length in milliseconds
        """
        self.title = title
        self.sample_rate = sample_rate
        self.bitrate = bitrate
        self.channels = channels
        self.length = length


class CurrentTrack(Track):
    """
    A class representing current track in Winamp.
    """

    def __init__(self,
                 title: str,
                 sample_rate: int,
                 bitrate: int,
                 channels: int,
                 length: int,
                 current_position: int,
                 playlist_position: int
                 ):
        """
        :param title: The track title in Winamp window. Usually in format {tracknum}. {artist} - {track_name} - Winamp
        :param sample_rate: The track sample rate
        :param bitrate: The track bitrate
        :param channels: Number of channels in the track
        :param length: The track length in milliseconds
        :param current_position: Track current position in milliseconds
        :param playlist_position: Track position in the playlist, starting from zero
        """
        super().__init__(title, sample_rate, bitrate, channels, length)
        self. current_position =  current_position
        self.playlist_position = playlist_position


class NoTrackSelectedError(Exception):
    """
    Exception raised when track is not selected in Winamp and one is required for requested operation.
    """


class Winamp:
    """
    a controller class for an open Winamp client.
    """

    NO_TRACK_SELECTED = 4294967295
    """
    A value Winamp returns for specific commands when the playlist is empty.
    """
    DEFAULT_NO_TRACK_MESSAGE = "No track selected in Winamp"


    def __init__(self):
        """
        Initialize a Winamp controller class. If Winamp client is not open during the initialization, method
        Winamp.connect() must be called afterwards before commands can be sent.
        """
        self.window_id = None
        self._version = None
        self.saved_playlist_path = None
        self.previous_track_title = None
        self.custom_assets = False
        self.connect()
        self.winamp_version = self._version

    def connect(self):
        """
        Connect to a Winamp client.
        """
        self.window_id = win32gui.FindWindow("Winamp v1.x", None)
        self._version = self.fetch_version()
        #print(f"\t filename = {self.saved_playlist_path} !")

    def __ensure_connection(self):
        """
        Raise an exception if no Winamp client is connected, otherwise do nothing.

        :raises ConnectionError: If a connection to Winamp client is not established.
        """
        if self.window_id == 0:
            raise ConnectionError("No Winamp client connected")


    def send_command(self, command: Union[MenuCommand, int]) -> int:
        """
        Send WM_COMMAND message to Winamp. These commands are identical to pressing menus and buttons in the player.

        :param command: MenuCommand object or the ID of the message to send.
        :return: Response from Winamp. Should be zero if the command is processed normally.

        :raises ConnectionError: If a connection to Winamp client is not established.
        """

        self.__ensure_connection()

        if isinstance(command, MenuCommand):
            command = command.value

        return win32api.SendMessage(self.window_id, WM_COMMAND, command, 0)

    def send_user_command(self, command: Union[UserCommand, int], data: int = 0) -> int:
        """
        Send WM_USER message to Winamp API. These commands are a programmatic way to communicate with the Winamp API.

        :param command: UserCommand object or the ID of the message to send.
        :param data: Data to send with the command. For some commands this value affects the returned information.
        :return: Response from the Winamp API.

        :raises ConnectionError: If a connection to Winamp client is not established.
        """

        self.__ensure_connection()

        if isinstance(command, UserCommand):
            command = command.value

        return win32api.SendMessage(self.window_id, WM_USER, data, command)

    @property
    def version(self) -> str:
        """
        The Winamp version.

        :raises ConnectionError: If a connection to Winamp client is not established.
        """
        self.__ensure_connection()

        return self._version

    @property
    def current_track(self) -> Optional[CurrentTrack]:
        """
        Fetch the current track.

        :return: CurrentTrack object that contains properties of the currently playing track, or None if no track is
        currently selected.
        """

        playlist_position = self.get_playlist_position()
        if not playlist_position:
            return None

        title = self.get_track_title()
        length, position = self.get_track_status()
        sample_rate, bitrate, num_channels = self.get_track_info()

        return CurrentTrack(title, sample_rate, bitrate, num_channels, length, position, playlist_position)

    def get_title(self) -> str:
        """
        Get the current track title.

        :return: Currently playing track title in format that is seen in Winamp's Window text. Usually in format
        '{track number}. {artist} - {track name} - Winamp'

        :raises ConnectionError: If a connection to Winamp client is not established.
        """
        global trackinfo_raw, artist, title
        self.__ensure_connection()
        trackinfo_raw = win32gui.GetWindowText(self.window_id)
        artist, title = extract_band_and_track_from_raw_title(trackinfo_raw)
        #gotta insert both into the class and only retrieve them  if they blah lah
        return title

    def get_artist(self) -> str:
        """
        Get the current track artist.

        :return: Currently playing track title in format that is seen in Winamp's Window text. Usually in format
        '{track number}. {artist} - {track name} - Winamp'

        :raises ConnectionError: If a connection to Winamp client is not established.
        """
        self.__ensure_connection()
        trackinfo_raw = win32gui.GetWindowText(self.window_id)
        artist, title = extract_band_and_track_from_raw_title(trackinfo_raw)
        #gotta insert both into the class and only retrieve them  if they blah lah
        return artist



    def get_trackinfo_raw(self) -> str:
        """
        Get the current raw track title.

        :return: Currently playing track title in format that is seen in Winamp's Window text. Usually in format
        '{track number}. {artist} - {track name} - Winamp'

        :raises ConnectionError: If a connection to Winamp client is not established.
        """
        self.__ensure_connection()
        return win32gui.GetWindowText(self.window_id)


    def fetch_version(self) -> str:
        """
        Fetch the Winamp version for currently open instance.

        :return: Winamp version number
        """

        # TODO: This can be improved to separate patch version from minor version
        # The version is formatted as 0x50yz for Winamp version 5.yz etc.
        hex_version = hex(self.send_user_command(UserCommand.WinampVersion))

        return f"{hex_version[2]}.{hex_version[4:]}"

    def get_playing_status(self) -> PlayingStatus:
        """
        Get current playing status.

        :return: The current playing status as PlayingStatus enumeration value.
        """
        gps_start  = time.perf_counter()
        status     = self.send_user_command(104)
        try:               retval = PlayingStatus(status)
        except ValueError: retval = PlayingStatus.Stopped
        gps_end = time.perf_counter()
        #print(f"\t(status of {retval} determined in {gps_end - gps_start} seconds)") #0.00034659996163100004s
        return retval

    def get_track_status(self) -> Tuple[int, int]:
        """
        Get the current track status.

        :return: A tuple containing track length and current track position in milliseconds.
        :raises NoTrackSelectedError: If no track is selected in Winamp.

        Sample use:
            track_length, track_position = get_track_status()
        """

        track_position = self.send_user_command(UserCommand.TrackStatus, 0)
        track_length   = self.send_user_command(UserCommand.TrackStatus, 1)

        if track_length == self.NO_TRACK_SELECTED:
            raise NoTrackSelectedError(self.DEFAULT_NO_TRACK_MESSAGE)

        return track_length * 1000, track_position

    def change_track(self, track_number: int) -> int:
        """
        Change the track to specific track number. If the track number is negative or bigger than the index of last
        playlist tract index, the first or last track is selected. Has no effect if playlist is empty.

        :param: Zero if the track was successfully changed.
        """

        return self.send_user_command(UserCommand.ChangeTrack, track_number)

    def get_playlist_position(self) -> Optional[int]:
        """
        Get current track position in the playlist.

        :return: The currently selected track position in the playlist, starting from 0.
        :return: Currently selected track position in the playlist starting from 0, or None if no track selected.
        """

        position = self.send_user_command(UserCommand.PlaylistPosition)
        if position == self.NO_TRACK_SELECTED:
            return None

        return position

    def seek_track(self, position: int) -> int:
        """
        Seek current track position to position.

        :param position: Seek position in milliseconds.
        :raises NoTrackSelectedError: If no track is selected in Winamp.
        """

        ret = self.send_user_command(UserCommand.SeekTrack, position)
        if ret == self.NO_TRACK_SELECTED:
            raise NoTrackSelectedError(self.DEFAULT_NO_TRACK_MESSAGE)

        return ret

    def set_volume(self, volume_level: int) -> int:
        """
        Set the players' playback volume.

        :param volume_level: Volume level in range from 0 to 255.
        :return: Zero if the volume was successfully set.
        :raises ValueError: If the volume level is outbounds.
        """

        if volume_level < 0 or volume_level > 255:
            raise ValueError("Volume level must be in range [0, 255]")

        return self.send_user_command(UserCommand.SetVolume, volume_level)

    def get_playlist_length(self) -> int:
        """
        Get the number of tracks in current playlist.

        :return: Number of tracks in the playlist.
        """

        return self.send_user_command(UserCommand.PlaylistLength)

    def get_track_info(self) -> Tuple[int, int, int]:
        """
        Get the currently selected track technical information.

        :return: Sample rate, bitrate and number of audio channels of currently playing track.
        :raises NoTrackSelectedError: If no track is selected in Winamp.
        """

        sample_rate = self.send_user_command(UserCommand.TrackInfo, 0)
        bitrate = self.send_user_command(UserCommand.TrackInfo, 1)
        num_channels = self.send_user_command(UserCommand.TrackInfo, 2)

        if sample_rate == 0 and bitrate == 0 and num_channels == 0:
            raise NoTrackSelectedError("No track selected in Winamp")

        return sample_rate, bitrate, num_channels

    def dump_playlist(self) -> int:
        """
        Dump the current playlist into file WINAMPDIR/winamp.m3u. WINAMPDIR is by default located in
        C:/Users/user/AppData/Roaming/Winamp/.

        :return: The position of currently playing track in the playlist, starting from 0.
        """
        #print ("\t\tabout to dump playlist............")
        returnValue = self.send_user_command(UserCommand.DumpPlaylist)
        if self.saved_playlist_path is None: self.saved_playlist_path = self.find_latest_winamp_playlist()
        return returnValue


    def get_playlist(playlist_filepath) -> Tuple[str, str]:
        """
        Get paths to tracks in a playlist. A playlist dump is required for this method except if a playlist file in
        specific location is desired.

        This method opens a playlist file in given path and decodes its contents into a list of track paths.
        The default location for playlist files is C:/Users/user/AppData/Roaming/Winamp/. For UTF-8 support, playlist
        file with extension .m3u8 should be used instead of .m3u.

        :param playlist_filepath: Path to the playlist file
        :return: List of absolute paths to all tracks in given playlist
        """

        # The playlist file is encoded in utf-8-sig and has redundant BOM characters
        with open(playlist_filepath, "r", encoding="utf-8-sig") as playlist_file:
            #open(playlist_filepath, "r", encoding="utf-8"    ) as playlist_file:
            lines = playlist_file.read().splitlines()

        return [line for line in lines if line and not line.startswith("#")]  # Exclude comments and empty lines




    #def get_current_track_file_path_FAIL(self) -> Optional[str]:
    #    """
    #    Get the file path of the currently playing track.
    #
    #    :return: The file path of the current track, or None if no track is selected.
    #    """
    #    playlist_position = self.get_playlist_position()
    #    if playlist_position is None:
    #        return None
    #     # Dump the playlist to a temporary file
    #    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8-sig') as temp_playlist_file:
    #        temp_playlist_file.write('\n'.join(self.get_playlist()))
    #        temp_playlist_path = temp_playlist_file.name
    #     # Read the temporary playlist file to get the track file path
    #    with open(temp_playlist_path, 'r', encoding='utf-8-sig') as temp_playlist_file:
    #        lines = temp_playlist_file.readlines()
    #        if 0 <= playlist_position < len(lines):
    #            return lines[playlist_position].strip()
    #        else:
    #            return None


    def find_latest_winamp_playlist(self) -> str:
        """
        Find the most recent Winamp playlist file in the user's AppData\Roaming directory.

        :return: The path to the most recent winamp.m3u file, or an empty string if not found.

        # Example usage
        self.saved_playlist_path = self.find_latest_winamp_playlist()
        print(f"The most recent Winamp playlist is located at: {saved_playlist_path}")
        """
        appdata_roaming = Path(os.getenv('APPDATA', ''))
        winamp_dirs = [d for d in appdata_roaming.glob('*winamp*') if d.is_dir()]

        latest_file = None
        latest_mtime = 0

        for winamp_dir in winamp_dirs:
            playlist_files = winamp_dir.glob('winamp.m3u8')
            for playlist_file in playlist_files:
                if playlist_file.stat().st_mtime > latest_mtime:
                    latest_mtime = playlist_file.stat().st_mtime
                    latest_file = playlist_file

        return str(latest_file) if latest_file else ''


    def get_current_track_file_path(self) -> Optional[str]:
        """
        Get the file path of the currently playing track.

        :return: The file path of the current track, or None if no track is selected or if the class is not properly set up.
        """
        # Check if self is of type Winamp or any other type you expect
        #if isinstance(self, Winamp):
        #    return None  # or handle this case as needed if self is not an instance of the expected type

        gctfp_start = time.perf_counter()

        w.dump_playlist()
        playlist_position = self.get_playlist_position()
        if playlist_position is not None:
            print(f"\t\t {playlist_position} = playlist position")
        else:
            return None

        print(f"saved_playlist= {self.saved_playlist_path}")
        with open(self.saved_playlist_path, 'r', encoding='utf-8-sig') as temp_playlist_file:
            lines = [line.strip() for line in temp_playlist_file if not line.startswith('#')]

        try:
            #f 0 <= (playlist_position+1) < len(lines):
            if 0 <= (playlist_position  ) < len(lines):
                retval = lines[playlist_position].strip()
                if retval.startswith('\\'): retval = f'C:{retval}'
                print(f"\t THE FILE = {retval}")
                return retval
            else:
                return None
        except Exception as e:
            print(f"An error occurred while reading the temporary playlist file: {e} [X1!]")
            return None
        finally:
            # Clean up the temporary file?
            # nah why bother? if os.path.exists(temp_playlist_path): os.remove(temp_playlist_path)
            pass
        gctfp_end = time.perf_counter()
        logger.debug(f"\t\tget_current_track_file_path took {gctfp_end - gctfp_start:.3f} s")

def strip_winamp_title_suffixes(info):
    winamp_title_suffixes_to_strip = [" - Winamp", " ***", " [Paused]", " [Stopped]"]
    suffix = None
    for suffix in winamp_title_suffixes_to_strip:
        logger.debug(f"⏸⏸⏸ Checking if {info} ends with {suffix}")
        if info.endswith(suffix):
            info = info[:-len(suffix)]
            logger.debug(f"⏸⏸⏸ Stripped suffix. New info: {info}")
    return info


def extract_band_and_track_from_raw_title(trackinfo_raw: str) -> Tuple[str, str]:
    import re

    # Remove everything up to and including "*** "
    # trackinfo_stripped = re.sub(r'^.*\*\*\* \d+\. ', '', trackinfo_raw)

    # On second thought, sometimes it's broken in mid-3-asterisks, so:
    # we should really just remove everything up to and including "* "
    trackinfo_stripped = re.sub(r'^.*\* \d+\. ', '', trackinfo_raw)
    #print(f"Stripped Info: 1: {trackinfo_stripped}")

    # Remove the number followed by a period
    trackinfo_stripped = re.sub(r'^\d+\. ', '', trackinfo_stripped)
    #print(f"Stripped Info: 2: {trackinfo_stripped}")

    # Strip off " - Winamp" and anything after it
    #rackinfo_stripped = re.sub(                r' - Winamp.*$'         , '' , trackinfo_stripped)
    #rackinfo_stripped = re.sub(             r' ?-? ?Winamp.*$'         , '' , trackinfo_stripped)
    #print(f"Stripped Info: 3: {                                               trackinfo_stripped}")

    trackinfo_stripped = re.sub(r' - Winamp *(?=[^ - Winamp ])[\s\*]*$' , '' , trackinfo_stripped)
    logger.debug(f"⏸⏸⏸ how is trackinfo_stripped={trackinfo_stripped} rn?")

    trackinfo_stripped = strip_winamp_title_suffixes(trackinfo_stripped)

    suffix=""
    winamp_title_suffixes_to_strip = [" - Winamp", " ***", " [Paused]", " [Stopped]"]
    while   suffix in winamp_title_suffixes_to_strip:
        for suffix in winamp_title_suffixes_to_strip:
            logger.debug(f"⏸⏸⏸does {trackinfo_stripped} and with {suffix}?")
            if trackinfo_stripped.endswith(suffix): trackinfo_stripped = trackinfo_stripped[:-len(suffix)]
            logger.debug(f"⏸⏸⏸final trackinfo_stripped={trackinfo_stripped}")



    # Split on "–" (endash) to get artist and track name
    # requires going into Winamp->Options->Title->Advanced Title formatting and changing the hyphen between artist and title into an endash
    if '–' not in trackinfo_stripped:                            #that – is an en-dash and not a hyphen!
        logger.debug(f'ERROR: can\'t find en-dash in "{trackinfo_raw}"\nYou probably need to go into Winamp->Preferences, to the "Titles" section (the 5th line on the left), to the "Advanced Title Formatting" section and make sure "Use Advanced title formatting when possible" is checked, and change the hypen (-) after %artist% into an en-dash (–).\nI prefer the following avanced title display format:\n[%artist% – ]$if2(%title%,$filepart(%filename%))')
        return "", ""

    artist, track = trackinfo_stripped.split('–', 1)     #that – is an en-dash and not a hyphen!
    artist = artist.strip()
    track  = track .strip()
    logger.debug(f"\t⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉⁉ Artist = '{artist}'\n\tSong   = '{track}'")
    return artist, track




#def update_rpc(w: Winamp):
#    #global previous_track_title
#    #global cleared
#    #global trackinfo_raw
#    #global artist
#    #global title
#
#    trackinfo_raw = w.get_trackinfo_raw()  # This is in format {tracknum}. {artist} - {track title} - Winamp
#    title         = w.get_title()          # This is in format {tracknum}. {artist} - {track title} - Winamp
#    #print(f"fresh title={title}")
#    #f trackinfo_raw !=   previous_track_title: #old
#    if title         != w.previous_track_title: #new
#        #.previous_track_title = trackinfo_raw  #old
#        w.previous_track_title = title          #new
#        trackinfo = trackinfo_raw.split(" - ")[:-1]
#        track_pos = w.get_playlist_position()   # rack position in the playlist
#        #GOAT let's be lazy and not compute this until we absolutely have to:
#        #artist, title = extract_band_and_track_from_raw_title(trackinfo_raw)
#        pos, now = w.get_track_status()[1] / 1000, time.time()              # Both are in seconds
#        if len(title) < 2: title = f"{title}"
#        if pos >= 4000000: pos = 0                 # Sometimes this is over 4 million if a new track starts
#        start = now - pos
#
#        if w.custom_assets: # If boolean custom_assets is set true, get the asset key and text from album_covers.json
#            large_asset_key, large_asset_text = get_album_art(track_pos, artist)
#        else:
#            large_asset_key  = "logo"
#            large_asset_text = "Winamp v" + w.winamp_version
#        #this was for updated discord: w.rpc.update(details=track_name, state=f"by {artist}", start=int(start), large_image=large_asset_key, small_image=small_asset_key, large_text=large_asset_text, small_text=small_asset_text)
#        cleared = False




def get_album_art(track_position: int, artist: str):
    """
    Dump current playlist into C:\\Users\\username\\Appdata\\Roaming\\Winamp\\Winamp.m3u8. Then read the path of current
    track from the file and find the album name from it. If album has corresponding album name with key in file
    album_covers.json, return the asset key and album name. Otherwise return default asset key and text. Also, this
    function assumes the music directory structure is like artist\\album\\tracks. If the folder structure is something
    else, the album_name variable may not be the album name and you need to check these manually.
    This function is used only if custom_assets is set to True and album_covers.json is found.

    :param track_position: Current track's position in the playlist, starting from 0
    :param artist: Current track's artist. This is needed in case album name is in exceptions i.e. there are multiple
    albums with same name
    :return: Album asset key and album name. Asset key in api must be exactly same as this key.
    """

    w.dump_playlist()
    find_latest_winamp_playlist()
    appdata_path = os.getenv("APPDATA")
    # Returns list of paths to every track in playlist which are in format
    # 'path_to_music_directory\\artist\\album\\track'
    tracklist_paths = w.get_playlist(f"{appdata_path}\\Winamp\\Winamp.m3u8")
    # Get the current track's directory path
    track_path = os.path.dirname(tracklist_paths[track_position])
    # Get the tail of the path i.e. the album name
    album_name = os.path.basename(track_path)

    large_asset_text = album_name
    # If there are multiple albums with same name, and they are added into exceptions file, use 'Artist - Album' instead
    if album_name in album_exceptions:
        album_key = f"{artist} - {album_name}"
    else:
        album_key = album_name
    try:
        large_asset_key = album_asset_keys[album_key]
    except KeyError:
        # Could not find asset key for album cover. Use default asset and asset text instead
        large_asset_key = default_large_key
        if default_large_text == "winamp version":
            large_asset_text = "Winamp v" + w.winamp_version
        elif default_large_text == "album name":
            large_asset_text = album_name
        else:
            large_asset_text = default_large_text

    if len(large_asset_text) < 2:
        large_asset_text = f"Album: {large_asset_text}"

    return large_asset_key, large_asset_text


def initialize_and_get_winamp_object():
    winamp_init_start = time.perf_counter()
    #global w, custom_assets, winamp_version

    # Get the directory where this script was executed to make sure Python can find all files.
    path_of_this_file = os.path.dirname(__file__)

    # Load current settings to a dictionary and assign them to variables. If settings file can't be found, make a new one
    # with default settings.
    #print(f"settings file would be at: {path_of_this_file}\\winamp-rpc-settings.json")
    try:
        with open(f"{path_of_this_file}\\winamp-rpc-settings.json") as settings_file:
            import json
            settings = json.load(settings_file)
    except FileNotFoundError:
        settings = {"_comment": "Default_large_asset_text 'winamp version' shows your Winamp version and 'album name' "
                                "the current playing album",
                    "client_id": "default",
                    "default_large_asset_key": "logo",
                    "default_large_asset_text": "winamp version",
                    "small_asset_key": "playbutton",
                    "small_asset_text": "Playing",
                    "custom_assets": False}
        with open(f"{path_of_this_file}\\winamp-rpc-settings.json", "w") as settings_file:
            import json
            json.dump(settings, settings_file, indent=2)
        #too much info: print("Could not find winamp-rpc-settings.json .... Made new settings file with default values.")

    client_id = settings["client_id"]
    default_large_key = settings["default_large_asset_key"]
    default_large_text = settings["default_large_asset_text"]
    small_asset_key = settings["small_asset_key"]
    small_asset_text = settings["small_asset_text"]
    custom_assets = settings["custom_assets"]
    if client_id == "default": client_id = "507484022675603456"
    #print("setting w to winamp")
    w = Winamp()
    #rpc = Presence(client_id)  #discord stuff
    #rpc.connect()              #discord stuff

    winamp_version = w.version
    previous_track_title = ""
    cleared = False

    # If boolean custom_assets is set True, try to load file for album assets and album name exceptions.
    # Files for album cover assets and album name exceptions are loaded only when starting the script so restart is
    # needed when new albums are added
    if w.custom_assets:
        try:
            with open(f"{path_of_this_file}\\album_name_exceptions.txt", "r", encoding="utf8") as exceptions_file:
                album_exceptions = exceptions_file.read().splitlines()
        except FileNotFoundError:
            print("Could not find album_name_exceptions.txt. Default (or possibly wrong) assets will be used for duplicate album names.")
            album_exceptions = []
        try:
            with open(f"{path_of_this_file}\\album_covers.json", encoding="utf8") as data_file:
                album_asset_keys = json.load(data_file)
        except FileNotFoundError:
            print("Could not find album_covers.json. Default assets will be used.")
            w.custom_assets = False
    winamp_init_end = time.perf_counter()
    #print(f"\t(winamp init took {winamp_init_end - winamp_init_start} seconds)") # 0.004s- 0.0005
    return w




if __name__ == "__main__":
    test_examples()


