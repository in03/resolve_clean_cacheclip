import os
import stat
import subprocess
from pyfiglet import Figlet
import sys
import time
#import inspect
from dotenv import load_dotenv
from pyclickup import ClickUp
from colorama import init
from colorama import Fore, Back, Style
from fuzzywuzzy import fuzz
from pathlib import Path

f = Figlet(font='slant')
print (f.renderText('Resolve/Clickup Cache Cleaner'))

print("This script will mark files for deletion!\n" +
      "Follow prompts carefully!\n")

time.sleep(5)

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
######################### GET CLICKUP TASKS ###############################
###########################################################################

print(Fore.MAGENTA + "\nInstantiating clickup API")

# Get environment variables
clickup = ClickUp(os.getenv("CLICKUP_TOKEN"))
watch_space = os.getenv("WATCH_SPACE")
watch_list = os.getenv("WATCH_LIST")

print(Fore.GREEN + "Accessing team")
main_team = clickup.teams[0]

# Access SPACE
print(Fore.GREEN + f"Accessing \"{watch_space}\" space")
for space in main_team.spaces:
    if space.name == watch_space:
        main_space = space
        break

# Error handling if SPACE is unavailable
try: 
    main_space
except NameError:
    print(Fore.RED + f"Couldn't find \"{watch_space}\" space specified in config file.")
    print("The following spaces are available:\n")
    for space in main_team.spaces:
        print(" -", space.name)
    print(Fore.RED + "\nAborting...")
    sys.exit(1)
    
# Access LISTS within PROJECT
print(Fore.GREEN + f"Accessing \"{watch_list}\" list")
for project in main_space.projects:
    for list in project.lists:
        if list.name == watch_list:
            main_list = list
            break

# Error handling if PROJECT is unavailable
try: 
    main_list
except NameError:
    print(Fore.RED + f"Couldn't find \"{watch_list}\" list specified in config file.")
    print("The following lists are available:\n")
    for project in main_space.projects:
        for list in project.lists:
            print(" -", list.name)
        print(Fore.RED + "\nAborting...")
        sys.exit(1)        
        
print(main_list)

print(Fore.GREEN + "Getting low priority project tasks...")
tasks = main_list.get_all_tasks(include_closed=True)

low_priority_tasks = []
for task in tasks:
    #print(f"Task: \"{task.name}\" Status: \"{task.status.status}\"")
    #inspect.getmembers(task.status)
    if (str(task.status.status).lower() in os.getenv('HIGH_PRIORITY')):
        print(f"Ignoring high priority task: \"{task.name}\"")
        continue
    else:
        low_priority_tasks.append(task)

if len(low_priority_tasks) == len(tasks):
    print(Fore.RED + "All tasks have been deemed low priority. Something is probably wrong. Have the space statuses changed?")
    sys.exit(1)

elif len(low_priority_tasks) == 0:
    print(Fore.RED + "No low priority tasks found. Something is probably wrong. Have the space statuses changed?")
    sys.exit(1)

###########################################################################
################ GET PROJECTS WITH cache MEDIA ########################
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

# Check go ahead
# print(low_priority_tasks)
# winner = sorted(comp, key=lambda dct: dct['ratio']).pop()
# low_priority_tasks.sort(key=lambda task.status.status)
for task in low_priority_tasks:
    print(f"\"{task.name}\"|{task.status.status}")
go_ahead = input(Fore.YELLOW + "\nIf a match is found for one of the projects above, its cache directory will be marked for deletion.\n" +
            "Type 'Yes', 'No', or 'Choose' if you would like to approve each deletion one by one.\n")

choose = False
if "n" in go_ahead.lower():
    print(Fore.RED + "\nCancelling...")
    sys.exit(2)
elif "y" in go_ahead.lower():
    choose = False
    print(Fore.GREEN + "\nContinuing.")
elif "c" in go_ahead.lower():
    choose = True
    print(Fore.GREEN + "\nContinuing with caution.")
else:
    print(Fore.RED + "\nInvalid response. Exiting.")
    sys.exit(1)


valid_project_folders = []
print(Fore.GREEN + "Getting project media cache folders...")
project_folders = next(os.walk(media_dir))[1]
for project in project_folders:
    project_info = f"{media_dir}\\{project}\\info.txt"
    try:
        os.access(project_info, os.F_OK)
    except:
        continue
    else:
        valid_project_folders.append(project_info)

# Find all existing proejcts, determine name and path
existing_projects = []
inaccessible_folders = []
print(Fore.GREEN + "Reading info.txt files...")
for project_info in valid_project_folders:
    
    try:
        with open(project_info, "r+") as file:
            name = file.readlines()[2]
            name = name[14:]
            #print(f"'{name}' has cache folder.")
            path = os.path.abspath(os.path.join(project_info, '..'))
            existing_projects.append({'name':name, 'path': path})
    except:
        inaccessible_folders.append(project_info)
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