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
- Run `make inputs-pull` to pull the zipped static data from S3 and put it in `/inputs`
- Run `python asf_welsh_energy_consultation/analysis/produce_plots.py --local_data_dir <YOUR_LOCAL_DIR>`. You need to specify the path to the local
  directory where your local copy of the EPC data is/will be saved by replacing `<YOUR_LOCAL_DIR>` with the path to your "ASF_data" directory or equivalent.
  If you don't have a local directory for ASF core data, you can create a folder called "ASF_data" in your home directory. You can specify which
  batch of EPC data to download and MCS data to load from S3 by passing the `--epc_batch` and `--mcs_batch` arguments, both
  default to downloading/loading the newest data from S3, respectively. Run `python asf_welsh_energy_consultation/analysis/produce_plots.py -h` for more info.

The script should generate the following six plots which will be saved in your local repo in `outputs/figures`:

- `cumulative_retrofits.html`
- `electric_tenure.html`
- `installations_by_gas_status.html`
- `installations_by_rurality.html`
- `new_build_hp_cumulative.html`
- `new_build_hp_proportion.html`

It should generate a further 10 plots, five in English and five in Welsh, saved in `outputs/figures/english` and `outputs/figures/welsh`, respectively:

- `age_prop[_welsh].png`
- `epc_all[_welsh].html`
- `epc_hp_private_retrofit[_welsh].html`
- `epc_hp_private[_welsh].html`
- `hp_tenure[_welsh].html`

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

## Historical analysis

Versions/batches of data used for previous analysis are listed below.

April 2023 analysis:

- EPC: 2022_Q4_complete (preprocessed)
- mcs_installations_230315.csv
- mcs_installations_epc_full_230315.csv
- off-gas-live-postcodes-2022.xlsx - check [here](https://www.xoserve.com/a-to-z/) for updates
- rurality.ods - 2011 Rural Urban Classification for small area geographies, see [here](https://www.ons.gov.uk/methodology/geography/geographicalproducts/ruralurbanclassifications)

## Contributor guidelines

[Technical and working style guidelines](https://github.com/nestauk/ds-cookiecutter/blob/master/GUIDELINES.md)

---

<small><p>Project based on <a target="_blank" href="https://github.com/nestauk/ds-cookiecutter">Nesta's data science project template</a>
(<a href="http://nestauk.github.io/ds-cookiecutter">Read the docs here</a>).
</small>
