import os
import json
import glob
import sys
from pathlib import Path
from PIL import ImageFont, __version__ as PILLOW_VERSION
import ctypes

def get_windows_terminal_settings_path():
    """
    Constructs the path to Windows Terminal's settings.json file.
    """
    local_app_data = os.getenv('LOCALAPPDATA')
    if not local_app_data:
        print("Error: Could not locate LOCALAPPDATA environment variable.")
        sys.exit(1)

    settings_path = Path(local_app_data) / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"
    if not settings_path.exists():
        print(f"Error: settings.json not found at {settings_path}")
        sys.exit(1)

    return settings_path

def load_settings(settings_path):
    """
    Loads and parses the settings.json file.
    """
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings
    except Exception as e:
        print(f"Error reading settings.json: {e}")
        sys.exit(1)

def get_default_profile(settings):
    """
    Retrieves the default profile's fontFace and fontSize, checking both the profile and the defaults.
    Supports both direct keys and nested 'font' dictionary.
    """
    default_profile_id = settings.get("defaultProfile")
    if not default_profile_id:
        print("Error: defaultProfile not found in settings.json")
        sys.exit(1)

    profiles = settings.get("profiles", {}).get("list", [])
    default_profile = None
    for profile in profiles:
        if profile.get("guid", "").lower() == default_profile_id.lower():
            default_profile = profile
            break

    if not default_profile:
        print("Error: Default profile not found in profiles list.")
        sys.exit(1)

    # Initialize variables
    font_face = None
    font_size = None

    # Debugging output
    print("\n--- Default Profile Details ---")
    for key, value in default_profile.items():
        print(f"{key}: {value}")
    print("-------------------------------\n")

    # Check for direct fontFace and fontSize
    font_face = default_profile.get("fontFace")
    font_size = default_profile.get("fontSize")

    # If not found, check within 'font' dictionary
    if not font_face or not font_size:
        font_info = default_profile.get("font")
        if isinstance(font_info, dict):
            if not font_face:
                font_face = font_info.get("face")
                if font_face:
                    print("fontFace not found directly. Retrieved 'face' from 'font' dictionary.")
            if not font_size:
                font_size = font_info.get("size")
                if font_size:
                    print("fontSize not found directly. Retrieved 'size' from 'font' dictionary.")

    # If still not found, check profiles.defaults
    if not font_face or not font_size:
        defaults = settings.get("profiles", {}).get("defaults", {})
        # Check direct keys in defaults
        if not font_face:
            font_face = defaults.get("fontFace")
            if font_face:
                print("fontFace not found in profile. Retrieved from profiles.defaults.")
        if not font_size:
            font_size = defaults.get("fontSize")
            if font_size:
                print("fontSize not found in profile. Retrieved from profiles.defaults.")
        # If still not found, check within 'font' in defaults
        if not font_face or not font_size:
            font_info = defaults.get("font")
            if isinstance(font_info, dict):
                if not font_face:
                    font_face = font_info.get("face")
                    if font_face:
                        print("fontFace not found directly in defaults. Retrieved 'face' from 'font' dictionary in defaults.")
                if not font_size:
                    font_size = font_info.get("size")
                    if font_size:
                        print("fontSize not found directly in defaults. Retrieved 'size' from 'font' dictionary in defaults.")

    # Final check
    if not font_face:
        print("Error: fontFace not specified in the default profile or profiles.defaults.")
        sys.exit(1)

    if not font_size:
        print("Error: fontSize not specified in the default profile or profiles.defaults.")
        sys.exit(1)

    return font_face, font_size

def find_font_file(font_face):
    """
    Attempts to find the font file corresponding to the given font_face.
    """
    fonts_dir = Path("C:/Windows/Fonts")
    if not fonts_dir.exists():
        print("Error: Windows Fonts directory not found.")
        sys.exit(1)

    # Possible font file extensions
    extensions = ['*.ttf', '*.otf', '*.ttc']

    # Search for matching font files
    matching_fonts = []
    for ext in extensions:
        matching_fonts.extend(glob.glob(str(fonts_dir / ext)))

    # Normalize font_face for comparison
    normalized_font_face = font_face.lower().replace(" ", "")

    # Attempt to find the font file
    for font_path in matching_fonts:
        font_file = Path(font_path)
        font_name = font_file.stem.lower().replace(" ", "")
        if normalized_font_face in font_name:
            return font_file

    # If no match found, attempt more flexible matching
    for font_path in matching_fonts:
        font_file = Path(font_path)
        font_name = font_file.stem.lower().replace(" ", "")
        if normalized_font_face in font_name or font_name in normalized_font_face:
            return font_file

    print(f"Error: Could not find a font file matching '{font_face}' in {fonts_dir}")
    sys.exit(1)

def calculate_max_char_dimensions(font_path, font_size, characters):
    try:
        font = ImageFont.truetype(str(font_path), int(font_size))
    except Exception as e:
        print(f"Error loading font file: {e}")
        sys.exit(1)

    max_width  = 0
    max_height = 0

    print("--- Measuring Characters ---")

    for char in characters:                                 # Using getbbox to get the bounding box of the character
        try:
            bbox   = font.getbbox(char)
            width  = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
        except AttributeError:                              # For Pillow versions < 10.0, fallback to getsize
            width, height = font.getsize(char)
            print("Warning: 'getbbox' not available. Using 'getsize' instead.")

        print(f"Character '{char}': Width = {width} px, Height = {height} px")

        if width  > max_width:  max_width  = width
        if height > max_height: max_height = height

    print("-----------------------------\n")
    return max_width, max_height






def get_windows_scaling_factor():
    """
    Retrieves the Windows DPI scaling factor.
    """
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        dpi = user32.GetDpiForSystem()
        scaling_factor = dpi / 96  # 96 DPI is the default scaling (100%)
        return scaling_factor
    except Exception as e:
        print(f"Error retrieving DPI scaling factor: {e}")
        return 1  # Default to no scaling

def calculate_height_to_width_ratio(max_width, max_height, scaling_factor):
    """
    Calculates the height-to-width ratio after applying scaling.
    """
    scaled_max_width  = max_width  * scaling_factor
    scaled_max_height = max_height * scaling_factor
    ratio             = scaled_max_height / scaled_max_width if scaled_max_width != 0 else 0
    return scaled_max_width, scaled_max_height, ratio

def main():
    # Check Pillow version
    try:
        major_version = int(PILLOW_VERSION.split('.')[0])
    except:
        major_version = 0

    print(f"Pillow Version: {PILLOW_VERSION}")
    if major_version < 10:
        print("Warning: It's recommended to use Pillow version 10.0 or higher for optimal compatibility.\n")

    # Step 1: Locate settings.json
    settings_path = get_windows_terminal_settings_path()

    # Step 2: Load settings.json
    settings = load_settings(settings_path)

    # Step 3: Extract fontFace and fontSize
    font_face, font_size = get_default_profile(settings)
    print(f"Font Face: {font_face}")
    print(f"Font Size: {font_size}")

    # Step 4: Find the font file
    font_file = find_font_file(font_face)
    print(f"Font File: {font_file}\n")

    # Step 5: Calculate maximum character dimensions
    # Define a set of representative characters
    #characters_to_measure = ["|", "—", "⎯", "H", 'W', 'M', 'Q', 'O', '@', '&', 'A', 'B', 'C', 'g', 'j', 'y', 'p', 'q', '!', '?', ':']
    characters_to_measure = ["|", "⎯", "M"]

    max_width, max_height = calculate_max_char_dimensions(font_file, font_size, characters_to_measure)
    print(f"Maximum Character Width: {max_width} pixels")
    print(f"Maximum Character Height: {max_height} pixels\n")


    # Step 6: Retrieve DPI scaling factor
    scaling_factor = get_windows_scaling_factor()
    scaled_max_width, scaled_max_height, ratio = calculate_height_to_width_ratio(max_width, max_height, scaling_factor)
    print(f"Height-to-Width Ratio (Scaled): {ratio:.2f}\n\n")
    print(f"^^^but according to the windows terminal people, this is probably really 2\n\n")

    print(f"DPI Scaling Factor: {scaling_factor:.2f}\n")

    print(f"Scaled Maximum Character Width:  {scaled_max_width :.2f} pixels")
    print(f"Scaled Maximum Character Height: {scaled_max_height:.2f} pixels")



if __name__ == "__main__":
    main()
