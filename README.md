# MyoFE Tutorial Notebooks

This repository is created by Kurtis Mann and maintained by the Computational Biomechanics Lab at the University of Kentucky.  

The goal is for this repository to contain a sequence of notebooks that steps users through FEniCS usage/syntax ultimately up to embedding MyoSim and running ventricle simulations. This set up is avoiding Docker, and will instead use Anaconda to manage our environment. It is recommended that users gain familiarity with command line interfaces, though all executed commands should be in this file.
## Setting up your environment
We need the following:
- Anaconda (to manage our environment)
- Python (version 3.10.4)
- dolfin 2019.1.0

### Windows
Unfortunately, FEniCS is not supported for Windows. There is a pretty easy workaround it seems for going through Ubuntu on a Windows machine that will be shown here. The big picture steps we will be taking are:
- [Install and verify installation of wsl on Windows](Install-and-verify-intallation-of-wsl-on-Windows)
- [Install Ubuntu using the wsl command prompt](Install-ubuntu-using-the-wsl-command-prompt)
- Install Anaconda in Ubuntu
- Install Python using Anaconda in Ubuntu
- Clone this repository
- Create and activate the MyoFE environment
- Step through a test Jupyter notebook

#### Install/verify installation of wsl on Windows
#### Install Ubuntu using the wsl command prompt
#### Install Anaconda in Ubuntu
#### Install Python using Anaconda in Ubuntu
#### Clone this repository
#### Create and activate the MyoFE environment
#### Step through a test Jupyter notebook

First, make sure conda is installed. If you are unsure whether it is installed or not, you can check by doing the following:  
### Mac/Linux
Start a terminal session, and execute the command  
`conda list`  
If conda is properly installed, a list of installed packages for python and their versions will show up. If an error is encountered, [install conda](https://docs.anaconda.com/anaconda/install/)

_Kurtis, verify this on lab windows machine:_  
Open the Anaconda Prompt program, and execute  
`conda list`  
If conda is properly installed, a list of installed packages for python and their versions will show up. If an error is encountered, [install conda](https://docs.anaconda.com/anaconda/install/)

If conda is properly installed, within the terminal/command prompt, navigate to the repository's environment file `myofe_environment.env`. It is in the top level directory of this repository.


--------------------
Using an older environment file, I want to try to create an environment from it without having had to previously install fenics or anything.

Trying "conda env create -f environment.yml"

... doesn't look like we can do fenics on windows. However, trying to install ubuntu on this windows machine is so far easy..
https://docs.microsoft.com/en-us/windows/wsl/install

Exact steps: since wsl was already installed, I executed the command: wsl --install -d Ubuntu
It installed Ubuntu, I created a username and password. Now it seems that I'm in a linux environment.
Now I need to install conda in here some how: https://gist.github.com/kauffmanes/5e74916617f9993bc3479f401dfec7da

wget https://repo.continuum.io/archive/Anaconda3-2021.11-Linux-x86_64.sh (Within wsl terminal, and my computer is 64 bit find other versions https://repo.anaconda.com/archive/))
bash Anaconda3-2021.11-Linux-x86_64.sh
# read user agreement, enter 'yes'
#Now I have conda installed. Have to exit out and go back into Ubuntu for this to take effect.
#Now install python:
conda install -c conda-forge python
which python #check that python is installed, and has anaconda in its path
# Download repository (this will give environment file, and notebooks)
git clone https://github.com/CharlesMann/myofe_training_notebooks.git
go into directory, find environment.yml file:
conda env create -f environment.yml
conda activate myofe

jupyter-lab
# open the file 'test_notebook.ipynb' and execute each code block.
Close the browser window, and in the wsl terminal execute: ctrl + C
This gives the option to kill the jupyter-lab process.
