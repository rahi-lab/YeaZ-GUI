@REM create an environment from the spec-file.yml and activate it
conda env create -f spec-file.yml
conda activate YeaZ

@REM install the yeaz package in the environment
pip install -e .

@REM Get Reservoir and install it in the environment (Git LFS NEEDED)
git clone https://github.com/rahi-lab/YeaZ-toolbox.git
cd YeaZ-toolbox
pip install -e .
cd ..


@REM Echo a message to indicate the installation process is complete
echo "Installation completed. You can activate the environment using 'conda activate YeaZ'."