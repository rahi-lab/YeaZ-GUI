conda create -n YeaZ python=3.9
conda activate YeaZ

# Install pip
conda install -c anaconda pip

# Install pytorch with conda
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
# If you have macOS m1/m2 or a machine without GPU's, you need to install PyTorch for cpu. for more information visit https://pytorch.org/get-started/locally/

# Install requirements
pip install -r requirements.txt
pip install -e .

# Install pytorch with conda
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia


# Get Reservoir and install it in the environment (Git LFS NEEDED)
git clone https://github.com/rahi-lab/YeaZ-toolbox.git
cd YeaZ-toolbox
pip install -r requirements.txt
pip install -e .
cd ../

# Deactivate environment
conda deactivate