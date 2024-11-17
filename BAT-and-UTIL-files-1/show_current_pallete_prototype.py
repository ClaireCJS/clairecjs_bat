import ctypes
import sys

def get_console_colors():
    STD_OUTPUT_HANDLE = -11

    # Define the _COORD structure
    class _COORD(ctypes.Structure):
        _fields_ = [
            ("X", ctypes.c_short),
            ("Y", ctypes.c_short),
        ]

    # Define the _SMALL_RECT structure
    class _SMALL_RECT(ctypes.Structure):
        _fields_ = [
            ("Left", ctypes.c_short),
            ("Top", ctypes.c_short),
            ("Right", ctypes.c_short),
            ("Bottom", ctypes.c_short),
        ]

    # Define the CONSOLE_SCREEN_BUFFER_INFO structure
    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("dwCursorPosition", _COORD),
            ("wAttributes", ctypes.c_ushort),
            ("srWindow", _SMALL_RECT),
            ("dwMaximumWindowSize", ctypes.c_ulong),
        ]

    # Retrieve the handle to the console output
    handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    # Retrieve the console screen buffer info
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(csbi))

    # Extract the foreground and background color attributes
    foreground_color = csbi.wAttributes & 0x0F
    background_color = (csbi.wAttributes & 0xF0) >> 4

    return foreground_color, background_color

# Usage example
fg_color, bg_color = get_console_colors()
print(f"Current foreground color: {fg_color}")
print(f"Current background color: {bg_color}")




c_sharp_code_to_get_fg_and_bg_color_code_but_not_rgb_values_so_this_is_just_here_for_interest= """

        public static void PrintTable(bool compact)
        {
            string TestText = compact ? "  gYw  " : " gYw ";
            ConsoleColor[] colors = (ConsoleColor[])ConsoleColor.GetValues(typeof(ConsoleColor));
            // Save the current background and foreground colors.
            ConsoleColor currentBackground = Console.BackgroundColor;
            ConsoleColor currentForeground = Console.ForegroundColor;

            // first column
            Console.Write("\t ");
            if (compact) Console.Write(" ");
            Console.Write(AnsiDefaultBg);
            if (compact) Console.Write(" ");
            Console.Write(" ");

            for (int bg = 0; bg < AnsiBackgroundSequences.Count; bg += 1 + Convert.ToUInt16(compact))
            {
                Console.Write("  ");
                if (compact) Console.Write(" ");
                Console.Write(AnsiBackgroundSequences[bg]);
                if (compact) Console.Write(" ");
                if (AnsiBackgroundSequences[bg].Length == 3) Console.Write(" ");
            }
            Console.WriteLine();

            for (int fg = 0; fg <= TableColors.Count && fg <= AnsiForegroundSequences.Count; fg++)
            {
                Console.ForegroundColor = currentForeground;
                Console.BackgroundColor = currentBackground;

                Console.Write(fg == 0 ? AnsiDefaultFg : AnsiForegroundSequences[fg - 1]);
                Console.Write("\t");

                if (fg == 0) Console.ForegroundColor = currentForeground;
                else Console.ForegroundColor = colors[TableColors[fg - 1]];

                for (int bg = 0; bg <= TableColors.Count; bg += 1 + Convert.ToUInt16(compact))
                {
                    if (bg > 0) Console.Write(" ");
                    if (bg == 0)
                        Console.BackgroundColor = currentBackground;
                    else Console.BackgroundColor = colors[TableColors[bg - (1 + Convert.ToUInt16(compact))]];
                    Console.Write(TestText);
                    Console.BackgroundColor = currentBackground;
                }
                Console.Write("\n");
            }
            Console.Write("\n");

            // Reset foreground and background colors
            Console.ForegroundColor = currentForeground;
            Console.BackgroundColor = currentBackground;
        }


"""

