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

print(Fore.MAGENTA + "This script will delete files. No output will be visible during deletion\n" +
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
###########################################################################
######################### GET CLICKUP TASKS ###############################
###########################################################################

print(Fore.MAGENTA + "\nInstantiating clickup API")
clickup = ClickUp(os.getenv("CLICKUP_TOKEN"))
watch_space = os.getenv("WATCH_SPACE")

print(Fore.GREEN + "Accessing team")
main_team = clickup.teams[0]

print(Fore.GREEN + f"Accessing \"{watch_space}\" space")
for space in main_team.spaces:
    if space.name == watch_space:
        main_space = space
        break

main_project = main_space.projects[0]
main_list = main_project.lists[0]

print(Fore.GREEN + "Getting low priority project tasks...")
tasks = main_list.get_all_tasks(include_closed=True)

low_priority_tasks = []
for task in tasks:
    #print(f"Task: \"{task.name}\" Status: \"{task.status.status}\"")
    #inspect.getmembers(task.status)
    if (str(task.status.status).lower() == "editing") or (str(task.status.status).lower() == "in review"):
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
for task in low_priority_tasks:
    print(f"\"{task.name}\"|{task.status.status}")
go_ahead = input(Fore.YELLOW + "\nIf a match is found for one of the projects above, its cached media will be deleted.\n" +
            "Type 'Yes', 'No', or 'Choose' if you would like to approve each deletion one by one.\n")

choose = False
if "n" in go_ahead.lower():
    print(Fore.RED + "Cancelling...")
    sys.exit(2)
elif "y" in go_ahead.lower():
    print(Fore.GREEN + "Continuing.")
elif "c" in go_ahead.lower():
    choose = True
    print(Fore.GREEN + "Continuing with caution.")
else:
    print(Fore.RED + "Invalid response. Exiting.")
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
            print(f"{name} has a registered local media cache folder.")
            path = os.path.abspath(os.path.join(project_info, '..'))
            existing_projects.append({'name':name, 'path': path})
    except:
        inaccessible_folders.append(project_info)
        continue

# Check existing projects have deletable media
existing_no_media = []
print(Fore.GREEN + "Checking for media...\n")
for project in existing_projects:
    for root, dirs, files in os.walk(project['path']):
        for file in files:
            # Found a deletable item?
            if file.endswith(deletable_ext):
                print(file)
                # waste no more time
                break


    # This project had none?
    else:
        print(Fore.YELLOW + f"Existing project \"{project['name']}\" has no deletable media. Skipping.")
        existing_no_media.append(project)
        existing_projects.remove(project)

if len(inaccessible_folders) > 0:
    print(Fore.YELLOW + f"{len(inaccessible_folders)} valid projects could not be accessed.")

if len(existing_no_media) > 0:
    print(Fore.YELLOW + f"{len(existing_no_media)} valid, accessible projects contained no deletable cache media\n")
    for existing in existing_projects:
        print(f"- {existing['name']}")

# Lists for later use
deleted = []
not_deleted = []

if len(existing_projects) == 0:
    print(Fore.RED + "Found no existing projects with cache media. Exiting.")
    sys.exit(1)
else:
    print(Fore.GREEN + f"Found {len(existing_projects)} projects with cache media.")
    for project in existing_projects:
        #print(project['name'])
        for task in low_priority_tasks:

            # Temporary list for comparison 
            # ( must not accrue each loop!)
            comp = []

            ratio = fuzz.ratio(str(task.name), str(project['name']))
            comp.append({'task_name': task.name, 'name': project['name'], 'ratio': ratio})
            winner = sorted(comp, key=lambda dct: dct['ratio']).pop()
            if (winner.get('ratio') > int(os.getenv("FUZZY_CONFIDENCE_THRESHOLD"))):
                print(Fore.GREEN + f"{winner.get('task_name')} - {winner.get('ratio')}% confident")
                print(f"Found match for {project['name']}.")
                if choose == True:
                    confirm = input(Fore.YELLOW + "Definitely delete? Yes/No\n")
                if "n" in confirm:
                    print(Fore.YELLOW + "Skipping.")
                    not_deleted.append(project['name'])
                    continue
                try:
                    os.chmod(project['path'], stat.S_IWUSR)
                except IOError:
                    print("Couldn't change directory permissions.\nAttempting to delete anyway.")
                else:
                    print("Deleting cache media files.")

                path_to_deletables = (f"{project['path']}\\*{deletable_ext}")
                deletables_confirm = input(f"Path for deletable items is: {path_to_deletables} Continue?\n")
                if "y" not in deletables_confirm:
                    print("Aborting")
                    sys.exit(2)
                
                try:
                    #shutil.rmtree(project['path'])
                    # Seems only permissible way to achieve on QNAP NAS used in testing
                    #subprocess.run(["DEL", "/F/Q/S", path_to_deletables, "> NUL"]) # No STDOUT
                    subprocess.run(["DEL", "/F/Q/S", path_to_deletables], shell=True)
                    print(f"Deleted cache files in \"{project['name']}\"")
                except TypeError:
                    print("Error deleting cache media directory. Skipping.")
                    continue
                    

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