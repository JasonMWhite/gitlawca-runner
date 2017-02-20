# python_template
A Python template repo to save you some yak-shaving.

[![Build Status](https://travis-ci.org/JasonMWhite/python_template.svg?branch=master)](https://travis-ci.org/JasonMWhite/python_template)

## Requirements
   * Python 3.3+ (Tested on 3.3, 3.4, 3.5, 3.6)
   * Instructions may be slightly different for PC
   
### Python Installation Instructions for MacOS
   * Install Homebrew
      * ```/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"```
   * Update Homebrew
      * `brew update`
   * Install Python3
      * `brew install python3`

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
9. Code away!
10. When you're done, you can type `deactivate` to leave the virtual environment.

Repeat steps 7-10 each time you want to make changes.
(Step 8 will only be necessary if you've modified the requirements)
