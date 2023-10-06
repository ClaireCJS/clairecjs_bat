import os

def rename_files(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".jpg"):
                # prepare original file path
                original_path = os.path.join(root, filename)

                # split filename to extract date and original filename
                date_string, remaining_string = filename.split(' - ', 1)

                # get the name of the current folder
                folder_name = os.path.basename(os.path.abspath(root))

                # create new filename
                new_filename = f"{date_string} - {folder_name} - {remaining_string}"
                new_path = os.path.join(root, new_filename)

                # perform rename and print what it's doing
                print(f'Renaming "{original_path}" to "{new_path}"')
                os.rename(original_path, new_path)

# replace with your directory path
rename_files('.')

