# Prepping for cell acdc

Cell-acdc can do many things, including segmentation, however, we already have very good scripts to do deconvolution and nuclear segmentation that work in batch mode on the server, so rather than trying to work with big data interactively, it is probably easiest to run those scripts and then feed in raw and deconvolved images and the nuclear segmentation masks into cell acdc and then use it interactively to delete/add/correct/split/merge masks.

The only difficult thing is that cell-acdc has a very specific data structure, and so this repo contains scripts based on our deconvolution and masks folder structure and file naming in order to automatically create the correct data structure. It also contains instructions on how to install and use cell-acdc on the server. 

Since most of the heavy-lifting (deconvolution and segmentation) was performed before you use cell-acdc, you might find it easier to install cell acdc locally on your machine. As long as you have enough RAM to load the different channels and masks all at once into memory, then working like this with izbkingston mounted as a network drive might be easier/faster. But if your personal computer cannot cope, then you can use it from teh server, which requires a few more steps described below.

# Installing cell acdc

Up to date instructions for installing and using [cell-acdc](https://github.com/SchmollerLab/Cell_ACDC/tree/main) are available in the [detailed documentation](https://cell-acdc.readthedocs.io/en/latest/index.html), so if the commands here do not work, you might need to update what needs to be done from there.

1. If not present: install [mamba](https://github.com/conda-forge/miniforge)
2. Create Mamba environment:  `mamba create -n acdc python=3.10`
3. Activate environment: `mamba activate acdc`
4. Install some libraries: `conda install -c conda-forge pyqt qtpy pyqtgraph seaborn pytables bioio bioio-nd2`
5. Install the latest version of cell-acdc: `pip install "git+https://github.com/SchmollerLab/Cell_ACDC.git"`



## Before you start cell-acdc

1. Before you can run cell-acdc on the server, you need X windows to be active on your computer. For mac that means having **XQuartz** installed (and maybe iTerm instead of the normal terminal window, not sure), and for windows that means installing **Xming** and having Xlaunch active, as well as putty to connect to the server.
2. Make sure you have a conda environment called acdc with acdc installed (see above).
3. Your images have been deconvoled with our [Deconwolf pipeline](https://github.com/CellFateNucOrg/Deconwolf)
4. Your nuclei have been segmented with our [Cellpose-SAM pipeline](https://github.com/CellFateNucOrg/CPSAM)




Your data is organised as follows:



You start off with all your .nd2 files in a particular directory.

1) deconvolve your images. they should be in a subdirectory called dw/ and the files should have the same name but with a _dw.tif ending

2) perform segmentation with cellpose same. the files should be in the subdirectory dw/masks/ and have a _dw_mask.tif ending, or they could be in subfolders with the channel name, e.g dw/masks/masks_GFP/*_dw_mask.tif

3) edit the setup_acdc.sh script to point src_dir to the directory where you have the .nd2 files. then run it on slurm

```
sbatch setup_acdc.sh
```

your files with the acdc correct setup will be placed in a sub directory called acdc. 
