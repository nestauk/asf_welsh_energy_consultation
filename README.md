# asf_welsh_energy_consultation

This repo contains code for producing charts for ASF's April 2023 response to the Welsh Government's consultation on Wales' renewable energy targets.

The remainder of the charts in the response can be produced from code in the repo `asf_senedd_response`, as these are based on charts originally produced for a previous call for evidence.

## Setup

- Meet the data science cookiecutter [requirements](http://nestauk.github.io/ds-cookiecutter/quickstart), in brief:
  - Install: `direnv` and `conda`
- Clone the repo: `git clone git@github.com:nestauk/asf_welsh_energy_consultation.git`
- Navigate to your local repo folder
- Checkout the correct branch if not working on dev
- Run `direnv allow`
- Run `make install` to configure the development environment. This will:
  - Setup the conda environment
  - Configure `pre-commit`
  - Install packages listed in `requirements.txt`
- Activate conda environment: `conda activate asf_welsh_energy_consultation`
- Download the data:

  - `make inputs-pull` will pull the zipped data from S3 and put it in `/inputs`
  - Download `mcs_installations_230315.csv` and `mcs_installations_epc_full_230315.csv` from `asf-core-data` S3 bucket (they can be found under `outputs/MCS/`) and add them to `inputs/data/`- Perform additional setup in order to save plots:

  - Follow the instructions (here)[https://github.com/altair-viz/altair_saver/#additional-requirements] to install ChromeDriver, node, and the required packages into your conda environment.

- Change `[directories][data_directory]` in `config/base.yaml` to your local EPC data folder if necessary. The April 2023 analysis uses the "2022_Q4_complete" version of the EPC data.

- Run `python asf_welsh_energy_consultation/analysis/produce_plots.py`. This should generate six plots:
  - `cumulative_retrofits.html`
  - `electric_tenure.html`
  - `installations_by_gas_status.html`
  - `installations_by_rurality.html`
  - `new_build_hp_cumulative.html`
  - `new_build_hp_proportion.html`

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
