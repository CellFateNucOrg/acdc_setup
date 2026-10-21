# Prepping for cell acdc

Make sure you have a conda environment called acdc with acdc installed. and make sure the bioio nd2 library is installed too:

```
mamba activate acdc
pip install bioio-nd2
```

You start off with all your .nd2 files in a particular directory.

1) deconvolve your images. they should be in a subdirectory called dw/ and the files should have the same name but with a _dw.tif ending

2) perform segmentation with cellpose same. the files should be in the subdirectory dw/masks/ and have a _dw_mask.tif ending, or they could be in subfolders with the channel name, e.g dw/masks/masks_GFP/*_dw_mask.tif

3) edit the setup_acdc.sh script to point src_dir to the directory where you have the .nd2 files. then run it on slurm

```
sbatch setup_acdc.sh
```

your files with the acdc correct setup will be placed in a sub directory called acdc. 
