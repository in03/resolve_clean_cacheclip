import os
import stat
import subprocess
from pyfiglet import Figlet
import sys
import time
#import inspect
from dotenv import load_dotenv
from colorama import init
from colorama import Fore, Back, Style
from fuzzywuzzy import fuzz
from glob import glob

f = Figlet(font='slant')
print (f.renderText('Resolve/Clickup Cache Cleaner'))

print("This script will mark files for deletion!\n" +
      "Follow prompts carefully!\n")

# time.sleep(5)

# Change .env file to alter variables #
try:
    load_dotenv()
except Exception as e:
    print(e)
    input("Failed to load .env file. \nPress enter to continue...")
else:
    print(Fore.GREEN + "Loaded configuration from .env")

	
init(autoreset=True)

# Lists for later use
deleted = []
not_deleted = []


###########################################################################
#################### GET PROJECTS WITH CACHE MEDIA ########################
###########################################################################

print(Fore.MAGENTA + "\nSearching drive for corresponding projects")

media_dir = os.getenv("MEDIA_CACHE_DIR")
deletable_ext = os.getenv("CACHE_FILE_FORMAT")

# Check directory exists
try:
    os.access(media_dir, os.W_OK)
except:
    print(Fore.RED + f"Could not access \"{media_dir}\". Invalid path.")
    sys.exit(1)
    
print(Fore.GREEN + "Media cache directory exists and is writable")


text_files = []
print(Fore.GREEN + "Getting project media cache folders...")
print(media_dir)

for dirpath, dirs, files in os.walk(media_dir):  
  for filename in files:
    fname = os.path.join(dirpath,filename)
    if fname is 'Info.txt': 
      print(Fore.GREEN + dirpath)
      text_files.append(os.path.join(dirpath, 'Info.txt'))
    else:
        print(f"Scanned {fname}, ignoring...")
        break
    
    for dir in dirs:
        if dir is "Collaboration":
            try:
                path = os.path.join(dir,'Info.txt')
                os.access(path)
                text_files.append(path)
                print(Fore.GREEN + path)
            except:
                print(f"Scanned {dir}, empty...")

for text_file in text_files:
    print(text_file)

exit(0)

# Find all existing proejcts, determine name and path
existing_projects = []
inaccessible_folders = []
print(Fore.GREEN + "Reading info.txt files...")
for text_file in text_files:
    
    try:
        with open(text_file, "r+") as file:
            name = file.readlines()[2]
            name = name[14:]
            #print(f"'{name}' has cache folder.")
            path = os.path.abspath(os.path.join(text_file, '..'))
            existing_projects.append({'name':name, 'path': path})
    except:
        inaccessible_folders.append(text_file)
        continue


if len(existing_projects) == 0:
    print(Fore.RED + "Found no existing projects with cache directory. Exiting.")
    sys.exit(1)


else:
    print(Fore.YELLOW + f"Found {len(existing_projects)} projects with cache media.\n")
    print(Fore.RED + "MATCHING LOW PRIORITY PROJECTS")

    deletable = []
    
    for project in existing_projects:
        #print(project['name'])
        for task in low_priority_tasks:

            # Temporary list for comparison 
            # (must not accrue each loop!)
            comp = []


            ratio = fuzz.ratio(str(task.name), str(project['name']))
            comp.append({'task_name': task.name, 'name': project['name'], 'ratio': ratio})
            winner = sorted(comp, key=lambda dct: dct['ratio']).pop()
            if (winner.get('ratio') > int(os.getenv("FUZZY_CONFIDENCE_THRESHOLD"))):
                print(Fore.GREEN + f"{winner.get('task_name')} - {winner.get('ratio')}% confident")
                #print(f"Found match for {project['name']}.")
                deletable.append(winner)
                if choose == True:
                    confirm = input(Fore.YELLOW + "Definitely delete? Yes/No\n")
                    if "n" in confirm:
                        print(Fore.YELLOW + "Skipping.")
                        not_deleted.append(project['name'])
                        continue
                try:
                    os.chmod(project['path'], stat.S_IWUSR)
                except IOError:
                    print(Fore.RED + "Couldn't change directory permissions.\nAttempting to rename anyway")
                else:
                    print(Fore.YELLOW + "Appending ' - DELETE ME' to folder name\n")

                path_to_deletables = (f"{project['path']}")              
                try:
                    os.rename(path_to_deletables, path_to_deletables + " - DELETE ME")
                except:
                    print(Fore.RED + "Error renaming cache media directory. Skipping.")
                    continue
                            
    if len(deletable) == 0:
        print(Fore.GREEN + "There are no low-priority projects with matching deletable media.")
        sys.exit(0)

    input(Fore.MAGENTA + "Done! Two windows will open. One in Explorer with the cache files marked ' - DELETE ME', \n"
    +  "the other, a web browser to the login page of the NAS. Delete the marked cache files directly from the NAS file browser. \n"
    + "Press ENTER to open a window to the cache folders marked for deletion...")

    # Open browser to NAS login
    NAS_URL = f"rundll32 url.dll,FileProtocolHandler {os.getenv('NAS_ADDRESS')}"
    subprocess.run(NAS_URL)

    # Open directory to view deletable folders
    FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
    subprocess.run([FILEBROWSER_PATH, media_dir])


    input(Fore.MAGENTA + "I'm still here if you need to double check any of the paths above.\n" +
    "Press ENTER to exit...")
    sys.exit(0)

                    

### task attributes/properties ###

    #team_id: str
    #page: int = None
    #order_by: str = None
    #reverse: bool = None
    #subtasks: bool = None
    #space_ids: list = None
    #project_ids: list = None
    #list_ids: list = None
    #statuses: list = None
    #include_closed: bool = False
    #assignees: list = None
    #due_date_gt: int = None
    #due_date_lt: int = None
    #date_created_gt: int = None
    #date_created_lt: int = None
    #date_updated_gt: int = None
    #date_updated_lt: int = None