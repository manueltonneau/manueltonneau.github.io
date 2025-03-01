#!/bin/bash

#SBATCH --job-name=get_proxies
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4GB
#SBATCH --time=168:00:00
#SBATCH --output=outfiles/slurm_get_proxies_%j.out
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-user=mt4493@nyu.edu

DATE=$1

module purge

singularity exec \
        --bind /home/mt4493/resolv.conf:/etc/resolv.conf:ro \
        --overlay /scratch/mt4493/singularity/scraping.ext3:ro \
	    /scratch/work/public/singularity/cuda11.1-cudnn8-devel-ubuntu18.04.sif \
	    /bin/bash -c "source /ext3/env.sh; python3 get_proxies.py --date ${DATE}"