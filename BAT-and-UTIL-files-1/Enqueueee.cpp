// Created:  2004 Mar 25  - Adapted from torsius' WinampMagic 
// Modified: 2004 Dec 10  - jyeee
// Modified: 2020 May/Jun - modified by Claire Jane Sawyer to not auto-advance to enqueued song
//           2024         - finding out this doesn't seem to work under Windows 10 anymore


/*
	Usage: Enqueueee/WinampMagic.exe [-abe | --help ] file
	-a      Enqueue song immediately after currently playing song
	-b      Enqueue song before currently playing song
	-e      Enqueue song at the end of playlist

	NOTE: WINAMP MUST BE ON
*/


#include <stdio.h>
#include <windows.h>
#include <malloc.h>
#include "winamp.h"
#include <string>
using namespace std;

// hides console
#pragma comment(linker, "/subsystem:\"windows\" /entry:\"mainCRTStartup\"")

#define METASIZE 128

// for options
#define AFTER 0
#define BEFORE 1
#define END 2
// /

HWND hwndWinamp;

// returns how many bytes were copied to local buffer
unsigned long ReadWinampToLocal(void *remoteBuf, void *localBuf, unsigned long bufsize) {
	int isError;
	HANDLE hWinamp;
	unsigned long dWinamp;

	GetWindowThreadProcessId(hwndWinamp, &dWinamp);						// find the process id

	hWinamp = OpenProcess(PROCESS_ALL_ACCESS,false,dWinamp);			// open the process object
	if(hWinamp == NULL) return 0;

	isError = ReadProcessMemory(hWinamp, remoteBuf, localBuf, bufsize, NULL);

	CloseHandle(hWinamp);

	if (!isError) return       0;
	else          return bufsize;
}


int GetPlayingTrack() {
	return SendMessage(hwndWinamp,WM_WA_IPC,0,IPC_GETLISTPOS);
}


void enqueueFile(char* filepath) {
	// perhaps extend this to include playlists :) - but wait, Enqueueue already works with playlists! Is this an obsolte comment?
	hwndWinamp = FindWindow("Winamp v1.x",NULL);
	COPYDATASTRUCT cds;
	cds.dwData = IPC_PLAYFILE;
	cds.cbData = lstrlen(LPCTSTR(filepath)) + 1;
	cds.lpData = (void *) LPCTSTR(filepath);
	SendMessage(hwndWinamp, WM_COPYDATA, (WPARAM)NULL, (LPARAM)&cds);
}

int main(int argc, char* argv[])
{
	printf("* Enqueueue.exe!!\n");
	int option;
	if ( argc != 3 || strcmp(argv[1], "--help") == 0 )	{					/* Check for command-line options: */
		printf("Usage: %s [-abe | --help ] file\n-a\tEnqueue song immediately after currently playing song\n-b\tEnqueue song before currently playing song\n-e\tEnqueue song at the end of playlist\n\nNOTE: WINAMP MUST BE ON\n", argv[0]);
		return 1;
	}
	for (int i = 1; i < argc; i++)	{
		if      ( strcmp(argv[1], "-a") == 0 ) { option = AFTER;  }
		else if ( strcmp(argv[1], "-b") == 0 ) { option = BEFORE; }
		else if ( strcmp(argv[1], "-e") == 0 ) { option = END;	  }
		else {
			printf("Unknown option: %s\n", argv[i]);
			printf("Usage: %s [-abe | --help ] file\n-a\tEnqueue song immediately after currently playing song\n-b\tEnqueue song before currently playing song\n-e\tEnqueue song at the end of playlist\n\nNOTE: WINAMP MUST BE ON\n", argv[0]);
			return 1;
		}
	}

	char *returnVal;
	returnVal = (char *)malloc(MAX_PATH*sizeof(char));

	hwndWinamp = FindWindow("Winamp v1.x",NULL);
	if(hwndWinamp == NULL)	{
		// run winamp
		string song = "\"";
		song += argv[2];
		song += + "\"";
		ShellExecute(NULL,"open","C:\\Program Files\\Winamp\\winamp.exe",song.c_str(),NULL,SW_SHOWNORMAL);

		// not finding winamp ): oh no  huh?
		hwndWinamp = FindWindow("Winamp v1.x",NULL);
		if (hwndWinamp == NULL) {
			ShellExecute(NULL,"open","C:\\windows\\notepad.exe",NULL,NULL,SW_SHOWNORMAL);
		}
		enqueueFile(argv[2]);
		int numtracks = SendMessage(hwndWinamp,WM_WA_IPC,0,IPC_GETLISTLENGTH);
		SendMessage(hwndWinamp,WM_WA_IPC,numtracks,IPC_SETPLAYLISTPOS);
		return 1;
	}
	
    int currentPositionInCurrentSong = SendMessage(hwndWinamp,WM_WA_IPC,0,IPC_GETOUTPUTTIME);	//Store current position -Claire edit
	int numtracks                    = SendMessage(hwndWinamp,WM_WA_IPC,0,IPC_GETLISTLENGTH);
	printf("\t(currentPositionInCurrentSong is %i)\n",currentPositionInCurrentSong);
	if ( numtracks == 0 ) {
		enqueueFile(argv[2]); 
		SendMessage(hwndWinamp,WM_WA_IPC,numtracks,IPC_SETPLAYLISTPOS);
		SendMessage(hwndWinamp,WM_COMMAND,40045,0);
		return 0;
	}

	if ( option == END ) {															// insert target after everything
		enqueueFile(argv[2]); 
		SendMessage(hwndWinamp,WM_WA_IPC,numtracks,IPC_SETPLAYLISTPOS);
		SendMessage(hwndWinamp,WM_COMMAND,40045,0);
		return 0;
	}
	
	char** playlist;																// put the playlist into an array
	playlist = new char*[numtracks];
	for ( int i = 0; i < numtracks; i++ ) {
		ReadWinampToLocal((char *)SendMessage(hwndWinamp, WM_WA_IPC, i, IPC_GETPLAYLISTFILE), returnVal, MAX_PATH);
		playlist[i]= (char *)malloc(MAX_PATH*sizeof(char));
		strcpy(playlist[i],returnVal);
	}

	int currentTrack = GetPlayingTrack();											// get current track and clear playlist
	printf("\t(Current track is %i)\n",currentTrack);
	SendMessage(hwndWinamp,WM_WA_IPC,0,IPC_DELETE);

	// enqueue tracks back into the playlist
	for ( int j = 0; j < numtracks; j++ ) {
		if ( j == currentTrack && option == BEFORE) { enqueueFile(argv[2]);  }		//insert target to play before the current track
		enqueueFile(playlist[j]);
		if ( j == currentTrack && option == AFTER ) { enqueueFile(argv[2]);  }		// insert target after current track
	}
	delete[] playlist;

	// set to the correct track
	if        ( option == BEFORE ) { SendMessage(hwndWinamp,WM_WA_IPC,currentTrack,IPC_SETPLAYLISTPOS);	} 
	else if   ( option == AFTER  ) {
		////Default/original/out-of-the-box behavior for this script is currentTrack +1 but Claire doesn't like that because it means
		////that we auto-advance to the next song. Well, this program isn't "enqueueue and play" it's just "enqueueue". 
		////Play is out of scope. So no. Let's no longer do currentTrack+1 and instead just do currentTrack without the +1
		//ndMessage(hwndWinamp,WM_WA_IPC,currentTrack + 1,IPC_SETPLAYLISTPOS); //OLD
		SendMessage(hwndWinamp,WM_WA_IPC,currentTrack    ,IPC_SETPLAYLISTPOS); //NEW
	}
	
	//hit the play button - this is actually necessary, even if it's already playing, to prevent winamp from playing track #1 next
	SendMessage(hwndWinamp,WM_COMMAND,40045,0); 

	//restore our position to the original position in the song when we issued the command
	//this moves is away from "enqueue and play" functionality to strictly "enqueue" functionality
	//the playback cursor is basically set to the exact moment this script was run
	if ( option == AFTER ) {
		SendMessage(hwndWinamp,WM_WA_IPC,currentPositionInCurrentSong,IPC_JUMPTOTIME); // IPC_JUMPTOTIME sets the position in milliseconds of the current song (approximately).
	}

	free(returnVal);																		// thanks, torsius

	return 0;
}