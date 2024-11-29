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
- Run `make inputs-pull` to pull the zipped supplementary data from S3 and put it in `/inputs/data`. There will be one folder per historical analysis
  containing the supplementary data files as listed in the `Historical analysis` section below.
- Run `python asf_welsh_energy_consultation/analysis/produce_plots_and_stats.py --local_data_dir <YOUR_LOCAL_DIR>`. You need to specify the path to the local
  directory where your local copy of the EPC data is/will be saved by replacing `<YOUR_LOCAL_DIR>` with the path to your "ASF_data" directory or equivalent.
  If you don't have a local directory for ASF core data, you can create a folder called "ASF_data" in your home directory.
  - You can specify which batch of EPC data to download and MCS data to load from S3 by passing the `--epc_batch` and `--mcs_batch` arguments, both
    default to downloading/loading the newest data from S3, respectively.
  - You can specify which supplementary data folder to use by passing the `--supp_data` argument. It defaults to using the latest supplementary data folder.
  - To recreate the full October 2023 analysis, set the `--calculate_average_installations` argument to `True`. This will calculate some additional numbers on MCS installations per year included in the October 2023 response. For other historical analyses, this argument is not required and defaults to `False`.
  - Run `python asf_welsh_energy_consultation/analysis/produce_plots_and_stats.py -h` for more info.

The script should generate the following seven plots which will be saved in your local repo in `outputs/figures`:

- `cumulative_retrofits.html`
- `electric_tenure.html`
- `installations_by_gas_status.html`
- `installations_by_rurality.html`
- `new_build_hp_cumulative.html`
- `new_build_hp_proportion.html`
- `total_cumulative_installations.html`

It should generate a further 10 plots, five in English and five in Welsh, saved in `outputs/figures/english` and `outputs/figures/welsh`, respectively:

- `age_prop[_welsh].png`
- `epc_all[_welsh].html`
- `epc_hp_private_retrofit[_welsh].html`
- `epc_hp_private[_welsh].html`
- `hp_tenure[_welsh].html`

It will also generate a `stats.txt` text file containing some summary statistics.

## Skeleton folder structure

```
asf_welsh_energy_consultation/
├─ analysis/
│  ├─ produce_plots_and_stats.py - produces plots
│  ├─ unused_plots.py - unused plotting functions from August '22
├─ config
│  ├─ base.yaml - global variables
│  ├─ translation_config.py - English to Welsh translations for producing figures translated into Welsh
├─ getters/
│  ├─ get_data.py - getters for raw data
├─ pipeline/
│  ├─ plotting.py - functions for plotting
│  ├─ process_data.py - functions to process and enhance raw data
│  ├─ unused_processing.py - unused processing functions from August '22
inputs/
├─ data/
│  ├─ data_[YYYYMM]/ - data files, a mixture of csv, xlsx and ods
│  │  ├─ postcodes/ - individual subfolders for each postcode region
outputs/
├─ figures/ - where charts are saved
```

## Historical analysis

Versions of data used for previous analysis are listed below.

| Analysis      | EPC                                                               | MCS<sup>1</sup> | Postcodes<sup>2</sup>                                                                              | Postcode to OA<sup>3</sup>                                                                                                                                  | Off gas postcodes<sup>4</sup>                                                                                 | Rural-urban classification<sup>5</sup>                                                                             | Dwellings<sup>6</sup>                                                                                                                          | Tenure<sup>7</sup>                                                            |
| ------------- | ----------------------------------------------------------------- | --------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| November 2024 | 2024 Q1 complete (preprocessed, and preprocessed and deduplicated | 241113          | [February 2024](https://geoportal.statistics.gov.uk/datasets/e14b1475ecf74b58804cf667b6740706)     | [February 2024](https://geoportal.statistics.gov.uk/datasets/ons::postcode-to-oa-2021-to-lsoa-to-msoa-to-lad-february-2024-best-fit-lookup-in-the-uk/about) | [September 2024](https://www.xoserve.com/help-centre/supply-points-metering/supply-point-administration-spa/) | [2011](https://www.gov.uk/government/statistics/2011-rural-urban-classification-lookup-tables-for-all-geographies) | [2021 census](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/numberofdwellingsbyhousingcharacteristicsinenglandandwales) | [2021 census](https://www.ons.gov.uk/datasets/RM003/editions/2021/versions/1) |
| October 2023  | 2023 Q2 complete (preprocessed, and preprocessed and deduplicated | 231009          | [August 2023](https://geoportal.statistics.gov.uk/datasets/487a5ba62c8b4da08f01eb3c08e304f6/about) | [May 2022](https://geoportal.statistics.gov.uk/datasets/e7824b1475604212a2325cd373946235/about)                                                             | [2022](https://www.xoserve.com/help-centre/supply-points-metering/supply-point-administration-spa/)           | [2011](https://www.gov.uk/government/statistics/2011-rural-urban-classification-lookup-tables-for-all-geographies) | [2021 census](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/numberofdwellingsbyhousingcharacteristicsinenglandandwales) | [2021 census](https://www.ons.gov.uk/datasets/RM003/editions/2021/versions/1) |
| April 2023    | 2022 Q4 complete (preprocessed)                                   | 230315          | ONS postcode directory. Date unknown.                                                              | ONS data. Date unknown.                                                                                                                                     | [2022](https://www.xoserve.com/help-centre/supply-points-metering/supply-point-administration-spa/)           | [2011](https://www.gov.uk/government/statistics/2011-rural-urban-classification-lookup-tables-for-all-geographies) | Not used                                                                                                                                       | ONS data. Date unknown.                                                       |

# Data attributions

1. MCS Installations Database. Date represents internal processing date.
2. ONS Postcode Directory for the UK. Contains OS data © Crown copyright and database right 2024. Contains Royal Mail data © Royal Mail copyright and database right 2024.
   Source: Office for National Statistics licensed under the Open Government Licence v.3.0
3. ONS Postcode to OA to LSOA to MSOA to LAD Best Fit Lookup in the UK. Contains OS data © Crown copyright and database right 2024. Contains Royal Mail data © Royal Mail copyright and database right 2024.
   Source: Office for National Statistics licensed under the Open Government Licence v.3.0
4. Off-gas Postcode Register from Xoserve.
5. Rural Urban Classification Lookup table. Contains public sector information licensed under the Open Government Licence v3.0.
6. Number of dwellings by housing characteristics in England and Wales. Contains public sector information licensed under the Open Government Licence v3.0.
7. Accommodation type by type of central heating in household by tenure. Contains public sector information licensed under the Open Government Licence v3.0.

## Contributor guidelines

[Technical and working style guidelines](https://github.com/nestauk/ds-cookiecutter/blob/master/GUIDELINES.md)

---

<small><p>Project based on <a target="_blank" href="https://github.com/nestauk/ds-cookiecutter">Nesta's data science project template</a>
(<a href="http://nestauk.github.io/ds-cookiecutter">Read the docs here</a>).
</small>
