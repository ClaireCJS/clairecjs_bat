import os
import json
from datetime import datetime

def rename_files(directory):
    # store all file paths in a dict, key: filename, value: filepath
    file_paths = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_paths[file] = root

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".json"):
                with open(os.path.join(root, filename), 'r') as f:
                    data = json.load(f)
                    if "photos" in data:
                        for photo in data["photos"]:
                            if "creation_timestamp" in photo and photo["uri"].split('/')[-1] in file_paths:
                                # convert timestamp to date
                                timestamp = int(photo["creation_timestamp"])
                                dt_object = datetime.fromtimestamp(timestamp)
                                formatted_date = dt_object.strftime("%Y%m%d %H%M")

                                # prepare original file path
                                original_filename = photo["uri"].split('/')[-1]
                                original_path = os.path.join(file_paths[original_filename], original_filename)

                                # prepare new file path, keep the original file name
                                new_filename = formatted_date + ' - ' + original_filename
                                new_path = os.path.join(file_paths[original_filename], new_filename)

                                # print rename command
                                print(f'mv "{original_path}" "{new_path}"')

# replace with your directory path
rename_files('.')
