#!/bin/bash
#SBATCH --job-name=acdc_setup
#SBATCH --output=slurm_%x_%j.out
#SBATCH --time=0-2:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem 8GB
##SBATCH --gres=gpu:1

#### Config ####

src_dir=/mnt/meister.data/meli/20260916_ma_crest_sd_l3_PMW1566_PMW1567_L3/1566_w/1566_with_heat_shock
rawChannels=( BF GFP mCherry )
deconvolvedChannels=( GFP mCherry )


source $HOME/miniforge3/bin/activate acdc

mkdir -p ${src_dir}/acdc

python setup_acdc.py $src_dir --rawChannels ${rawChannels[@]} --deconvolvedChannels ${deconvolvedChannels[@]}

chmod ug+wx -R ${src_dir}/acdc
