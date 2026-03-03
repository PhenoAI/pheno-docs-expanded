---
title: "NutriMatch: harmonizing food composition databases with large language models for enhanced nutritional prediction"
date: "2026-01-21"
link: https://doi.org/10.1038/s44482-025-00001-7
image: 21dab351_image.png
categories:
  - "Diel logging"
  - "Nutrition"
  - "Segal lab"
  - "Pheno.AI"
  - "npj | digital public health"
  - "2026"
---

Jankelow A, Godneva A, Rein M, Samocha-Bonet D, Weissglas-Volkov D, Zohar S, Shor T, Segal E, [*npj | digital public health*](https://doi.org/10.1038/s44482-025-00001-7)



## Paper summary

Accurate analysis of dietary intake depends on linking food logs to food composition databases (FCDBs), yet these databases are often incomplete, inconsistent across regions, and difficult to harmonize at scale. In this study, the authors introduce **NutriMatch**, a scalable framework that leverages large language models (LLMs) and semantic embeddings to harmonize food composition databases across languages and regions and to impute missing nutrient values in a transparent and reproducible manner. NutriMatch aligns nutritionally equivalent food items across multiple FCDBs using embedding-based similarity, validates matches with an LLM acting as an automated judge, and enriches nutrient profiles by transferring missing values from matched reference foods 
s44482-025-00001-7.

The method was applied to the Israeli Human Phenotype Project (HPP), a deeply phenotyped cohort of over 10,000 adults who continuously log dietary intake via a mobile application linked to a local FCDB. Using NutriMatch, the authors expanded the HPP database from 21 recorded nutrients to 151 nutrients by harmonizing information from multiple international FCDBs, substantially increasing nutritional resolution while preserving cross-database consistency. Validation analyses demonstrated that two weeks of diet logging provide a stable and reproducible snapshot of long-term nutrient intake, supporting the use of short-term digital food logs for longitudinal phenotype prediction.

To assess the impact of nutrient enrichment, the authors evaluated predictive models linking dietary intake to a range of phenotypes, including body composition, blood biomarkers, continuous glucose monitoring metrics, and obesity status at two-year follow-up. Models incorporating the NutriMatch-expanded nutrient set consistently outperformed models based on age alone or basic macronutrients, with particularly strong gains for body fat measures, waist circumference, serum folate, and obesity prediction. Enriched nutrient profiles also revealed biologically coherent associations with metabolomic blood markers, highlighting the added explanatory value of micronutrients beyond standard dietary features.

Generalizability was demonstrated by applying the full NutriMatch pipeline to the Australian PREDICT cohort, a randomized clinical trial of individuals with prediabetes or early-stage type 2 diabetes. Nutrient imputations showed high concordance with the Australian reference database, and predictive models trained in HPP transferred to PREDICT without retraining, achieving improved performance compared with baseline nutrient models. Together, these results establish NutriMatch as a robust approach for harmonizing food composition databases, enriching dietary data at scale, and enabling cross-cohort nutritional analyses that improve diet–health modeling across populations and clinical contexts.

<br/>

![image](21dab351_image.png)