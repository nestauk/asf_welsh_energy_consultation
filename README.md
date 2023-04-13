# asf_welsh_energy_consultation

This repo contains code for producing charts for ASF's April 2023 response to the Welsh Government's consultation on Wales' renewable energy targets.

The remainder of the charts in the response can be produced from code in the repo `asf_senedd_response`, as these are based on charts originally produced for a previous call for evidence.

## Setup

- Meet the data science cookiecutter [requirements](http://nestauk.github.io/ds-cookiecutter/quickstart), in brief:
  - Install: `direnv` and `conda`
- Clone the repo: `git clone git@github.com:nestauk/asf_welsh_energy_consultation.git`
- Navigate to the repo folder
- Checkout the correct branch if not working on dev
- Run `make install` to configure the development environment:
  - Setup the conda environment
  - Configure `pre-commit`
- Run `direnv allow`
- Activate conda environment: `conda activate asf_welsh_energy_consultation`
- Install requirements: `pip install -r requirements.txt`
- Download the data:
  - `make inputs-pull` will pull the zipped data from S3 and put it in `/inputs`
  - Download `mcs_installations_230315.csv` and `mcs_installations_epc_full_230315.csv` from `asf-core-data` and add them to `inputs/data/`
- Perform additional setup in order to save plots:

  - Follow the instructions here - you may just need to run `conda install -c conda-forge vega-cli vega-lite-cli`

- Change `LOCAL_DATA_DIR` in `getters/get_data.py` to your local EPC data folder.

- Run `python asf_welsh_energy_consultation/analysis/produce_plots.py`. This should generate six plots:
  - `cumulative_retrofits.png`
  - `electric_tenure.png`
  - `installations_by_gas_status.png`
  - `installations_by_rurality.png`
  - `new_build_hp_cumulative.png`
  - `new_build_hp_proportion.png`

## Skeleton folder structure

```
asf_welsh_energy_consultation/
├─ analysis/
│  ├─ produce_plots.py - produces plots
│  ├─ unused_plots.py - unused plotting functions from August '22
├─ getters/
│  ├─ get_data.py - getters for raw data
├─ pipeline/
│  ├─ process_data.py - functions to process and enhance raw data
│  ├─ unused_processing.py - unused processing functions from August '22
inputs/
├─ data/ - data files, a mixture of csv, xlsx and ods
│  ├─ postcodes/ - individual subfolders for each postcode region
outputs/
├─ figures/ - where charts are saved
```

## Contributor guidelines

[Technical and working style guidelines](https://github.com/nestauk/ds-cookiecutter/blob/master/GUIDELINES.md)

---

<small><p>Project based on <a target="_blank" href="https://github.com/nestauk/ds-cookiecutter">Nesta's data science project template</a>
(<a href="http://nestauk.github.io/ds-cookiecutter">Read the docs here</a>).
</small>
