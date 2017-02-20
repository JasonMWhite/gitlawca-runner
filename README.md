# python_template
A Python template repo to save you some yak-shaving.


## Usage
1. Create an empty repository on Github for your project
2. Clone the repository locally into the name of your project
  * `git clone https://github.com/JasonMWhite/python_template.git my_project_name`
3. Create a virtual environment for your project
  * `python3 -m venv my_project`
4. Change to the directory of your project
  * `cd my_project_name`
5. Link the directory to your empty repository
  * `git remote add origin https://github.com/MyUsername/my_project_name.git`
6. Push the code to your repository
  * `git push -u origin master`
7. Activate the virtual environment
  * `source bin/activate`
8. Install local dependencies
  * `pip install -r requirements/dev.txt`
