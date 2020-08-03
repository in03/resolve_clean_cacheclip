import os
from dotenv import load_dotenv
from pyclickup import ClickUp

clickup = ClickUp("pk_305706_BAXPM5H41CTGBK809KCHAUB6YZYMBRAI")

main_team = clickup.teams[0]
for space in main_team.spaces:
    print(space.name)
    if space.name == "2. Projects":
        main_space = space
        break

for project in main_space.projects:
    print("Project:", project)
    for list in project.lists:
        print("List:", list)
        tasks = list.get_all_tasks(include_closed=True)
        for task in tasks:    
            print(task)