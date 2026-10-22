# Prepping for cell acdc

Cell-acdc can do many things, including segmentation, however, we already have very good scripts to do deconvolution and nuclear segmentation that work in batch mode on the server, so rather than trying to work with big data interactively, it is probably easiest to run those scripts and then feed in raw and deconvolved images and the nuclear segmentation masks into cell acdc and then use it interactively to delete/add/correct/split/merge masks.

The only difficult thing is that cell-acdc has a _very specific data structure_, and so this repo contains scripts based on our deconvolution and masks folder structure and file naming in order to automatically create the correct data structure. It also contains instructions on how to install and use cell-acdc on the server. 

Since most of the heavy-lifting (deconvolution and segmentation) was performed before you use cell-acdc, _you might find it easier to install cell acdc locally on your personal machine_. As long as you have enough RAM to load the different channels and masks all at once into memory, then working like this with izbkingston mounted as a network drive might be easier/faster. But if your personal computer cannot cope, then you can use it from the server, which requires a few more steps described below.

## A. Installing cell acdc

Up to date instructions for installing and using [cell-acdc](https://github.com/SchmollerLab/Cell_ACDC/tree/main) are available in the [detailed documentation](https://cell-acdc.readthedocs.io/en/latest/index.html), so if the commands here do not work, you might need to update what needs to be done from there.

1. If not present: install [mamba](https://github.com/conda-forge/miniforge)
2. Create Mamba environment:  `mamba create -n acdc python=3.11`
3. Activate environment: `mamba activate acdc`
4. Install the latest version of cell-acdc: `pip install "git+https://github.com/SchmollerLab/Cell_ACDC.git"`
5. Install some libraries: `mamba install -c conda-forge pyqt qtpy pyqtgraph seaborn pytables bioio bioio-nd2`

## B. Before you start cell-acdc

1. Before you can run cell-acdc on the server, you need X windows to be active on your computer. For mac that means having **XQuartz** installed (and maybe iTerm instead of the normal terminal window, not sure), and for windows that means installing **Xming** and having Xlaunch active, as well as putty to connect to the server.
2. Make sure you have a conda environment called acdc with acdc installed (see above).
3. Your images have been deconvoled with our [Deconwolf pipeline](https://github.com/CellFateNucOrg/Deconwolf)
4. Your nuclei have been segmented with our [Cellpose-SAM pipeline](https://github.com/CellFateNucOrg/CPSAM)

Your data should be organised as follows, where <src> is the name of the folder in which your .nd2 files are.

```
    <src>/
        somefile.nd2
        anotherfile.nd2
        dw/
            somefile_dw.tif
            somefile_dw_max.tif    ← skipped
            anotherfile_dw.tif
            masks/
                somefile_dw_mask.tif
                anotherfile_dw_mask.tif
```

### Setting up the cell-acdc data structure

Cell acdc has a very specific data structure that must be followed for you to use it. It does have its own data prep modules but since we need to add our own segmentation, it is easier doing it all with our own script that uses the data structure described above to create the right structure for acdc. 

- Clone this repository: `git clone git@github.com:CellFateNucOrg/acdc_setup.git`
- Edit the **setup_acdc.sh** script to point `src_dir` to the directory where you have the .nd2 files.
- Edit the list of `rawChannels`: rawChannels are all the channels in your .nd2 files (in the correct order!).
- Edit the list of `deconvolvedChannels`: deconvolvedChannels are all the channels in your _dw.tif files (in the correct order!).
- Make sure the names of the channels agree with whatever you used in the deconvolution scripts.
- Then run **setup_acdc.sh** it on slurm:
  
```
sbatch setup_acdc.sh
```

Your files with the acdc correct file structure will be placed in a sub directory called acdc. 

## C. Running cell-acdc on the server

1. Login to the server using `ssh -X username@izblisbon.izb.unibe.ch` the -X option is important to allow you to start X windows and the gui for ACDC.
2. Reserve a compute node with the following command: `salloc --x11 --mem=32GB --time=10:00:00 -p all --ntasks=2` the --x11 is again important for x windows forwarding. You can modify the time or memory requested. there is no need for GPUs since you have already segmented the files.
3. Activate the acdc environment: `mamba activate acdc`.
4. Start acdc by typing `acdc`. It may take a while to start up.

## D. Finishing a session on the server
1. Close the gui
2. Close your interactive session on the compute  node by typing `exit`. (otherwise you keep those resources busy until the time you allocated is up).

## E. Using cell-acdc

You can directly jump to the "Launch GUI" button to use the gui with your data.

There are a lot of great features you can do very easily on the gui, especially if you learn the keyboard shortcuts - hover over the buttons to get instructions, and check out the [user manual](https://cell-acdc.readthedocs.io/en/latest/tooltips.html).  

I particularly love the auto-pilot feature that lets you scroll through the segmented masks one by on at high magnification without having to zoom in and out all the time. 
