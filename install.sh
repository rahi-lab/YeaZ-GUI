# create an environment from the spec-file.yml and activate it
conda env create -f spec-file.yml
source activate YeaZ

# print the environment information to make sure that yeaz is activated
conda info --envs

# install the yeaz package in the environment
pip install -e .

# Get yeaz-toolbox and install it in the environment
git clone https://github.com/rahi-lab/LYN-track-and-trace.git
cd LYN-track-and-trace
pip install -e .
cd ../


# Echo a message to indicate the installation process is complete
echo "Installation completed. You can activate the environment using 'conda activate YeaZ'."
