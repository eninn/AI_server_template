import os, shutil, zipfile, glob

def unzip_file(zip_path, dest_folder, error_log_file):
    """Unzip a zip file to 'dest_folder' and log errors to 'error_log_file'"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_folder)
    except zipfile.BadZipFile:
        with open(error_log_file, 'a') as log_file:
            log_file.write(f"BadZipFile: {zip_path}\n")

def handle_split_zip(zip_part_path, dest_folder, error_log_file):
    """Unzip splited zip files and merge them to 'dest_folder' and log errors to 'error_log_file"""
    base_path = zip_part_path.split(".part")[0]
    part_files = sorted(glob.glob(f"{base_path}.part*"))
    
    output_zip_path = f"{base_path}_merged.zip"
    
    try:
        with open(output_zip_path, "wb") as f_out:
            for part_file in part_files:
                with open(part_file, "rb") as f_in:
                    shutil.copyfileobj(f_in, f_out)
        
        unzip_file(output_zip_path, dest_folder, error_log_file)
    except Exception as e:
        with open(error_log_file, 'a') as log_file:
            log_file.write(f"Error while handling split zip: {zip_part_path} - {str(e)}\n")
    finally:
        if os.path.exists(output_zip_path):
            os.remove(output_zip_path)

def process_zip_files_in_folder(target_folder, result_folder, error_log_file):
    """Process zip files in 'target_folder' and log errors to 'error_log_file'"""
    for root, dirs, files in os.walk(target_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(root, target_folder)
            dest_dir = os.path.join(result_folder, relative_path)

            os.makedirs(dest_dir, exist_ok=True)

            if file_name.endswith('.zip'):
                print(f"Unzipping: {file_path} to {dest_dir}")
                unzip_file(file_path, dest_dir, error_log_file)
            elif ".part" in file_name:
                if file_name.endswith('.part0'):
                    print(f"Merging and unzipping: {file_path} to {dest_dir}")
                    handle_split_zip(file_path, dest_dir, error_log_file)