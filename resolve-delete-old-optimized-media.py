import os
import stat
import shutil
import sys
#import inspect
from dotenv import load_dotenv
from pyclickup import ClickUp
from colorama import init
from colorama import Fore, Back, Style
from fuzzywuzzy import fuzz
from pathlib import Path


# Change .env file to alter variables #


try:
    load_dotenv()
except Exception as e:
    print(e)
    input("Failed to load .env file. \nPress enter to continue...")
else:
    print("Loaded configuration from .env")

	
init(autoreset=True)
###########################################################################
######################### GET CLICKUP TASKS ###############################
###########################################################################

print(Fore.GREEN + "Instantiating clickup API")
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

print(Fore.GREEN + "Getting low priority project tasks...\n")
tasks = main_list.get_all_tasks(include_closed=True)

low_priority_tasks = []
for task in tasks:
    #print(f"Task: \"{task.name}\" Status: \"{task.status.status}\"")
    #inspect.getmembers(task.status)
    if (str(task.status.status).lower() == "editing") or (str(task.status.status).lower() == "in review"):
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
################ GET PROJECTS WITH OPTIMIZED MEDIA ########################
###########################################################################

media_dir = os.getenv("OPTIMIZED_MEDIA_DIR")

# Check directory exists
try:
    os.access(media_dir, os.W_OK)
except():
    print(Fore.RED + f"Could not access \"{media_dir}\". Invalid path.")
    sys.exit(1)
print(Fore.GREEN + "Optimized media directory exists and is writable")

# Check go ahead
for task in low_priority_tasks:
    print(f"\"{task.name}\"|{task.status.status}")
go_ahead = input(Fore.YELLOW + "If a match is found for one of the projects above, its optimized media will be deleted.\n" +
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
print(Fore.GREEN + "Getting optimized media folders...")
project_folders = next(os.walk(media_dir))[1]
for project in project_folders:
    project_info = f"{media_dir}\\{project}\\info.txt"
    try:
        os.access(project_info, os.F_OK)
    except:
        continue
    else:
        valid_project_folders.append(project_info)

existing_projects = []
inaccessible_folders = []
print(Fore.GREEN + "Reading info.txt files...")
for project_info in valid_project_folders:
    
    try:
        with open(project_info, "r+") as file:
            project_name = file.readlines()[2]
            project_name = project_name[14:]
            project_path = os.path.abspath(os.path.join(project_info, '..'))
            existing_projects.append({'project_name':project_name, 'project_path': project_path})
    except:
        inaccessible_folders.append(project_info)
        continue

print(Fore.YELLOW + f"{len(inaccessible_folders)} folders were inaccessible or invalid optimized media directories and were skipped.")


if len(existing_projects) == 0:
    print(Fore.RED + "Found no existing projects with optimized media. Exiting.")
    sys.exit(1)
else:
    print(Fore.GREEN + "Found existing projects with optimized media.")
    for project in existing_projects:
        #print(project['project_name'])
        for task in low_priority_tasks:
            comp = []
            ratio = fuzz.ratio(str(task.name), str(project['project_name']))
            comp.append({'task_name': task.name, 'project_name': project['project_name'], 'ratio': ratio})
            winner = sorted(comp, key=lambda dct: dct['ratio']).pop()
            if (winner.get('ratio') > int(os.getenv("FUZZY_CONFIDENCE_THRESHOLD"))):
                print(Fore.GREEN + f"{winner.get('task_name')} - {winner.get('ratio')}%")
                print(f"Found match for {project['project_name']}.")
                if choose == True:
                    confirm = input(Fore.YELLOW + "Definitely delete? Yes/No\n")
                if "n" in confirm:
                    print(Fore.YELLOW + "Skipping.")
                    continue
                try:
                    os.chmod(project['project_path'], stat.S_IWUSR)
                except:
                    print("Couldn't change directory permissions.\nAttempting to delete anyway.")
                else:
                    print("Deleting optimized media directory.")
                try:
                    shutil.rmtree(project['project_path'])
                except:
                    print("Error deleting optimized media directory. Skipping.")
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