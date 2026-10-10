# Deliverable memo

Generated from `docs/spec/` via `scripts/deliverable_memo.py`.
Coverage freeze: **259/259** (`python scripts/spec_report.py`).

This is the per-document response: every DOC1 category and variable,
every DOC2 widget, mapped to the artefact that discharges it.

---

## DOC1 — categories and variables

| Id | Name | Model | Satisfied by |
|---|---|---|---|
| `M1.C1` | Historical enrollment time series | M1 | table: `data/ethiopia/enrollment_history.parquet` |
| `M1.C1.V1` | Lag-1 enrollment | M1 | `enrollment_lag_1y` |
| `M1.C1.V2` | Lag-2 enrollment | M1 | `enrollment_lag_2y` |
| `M1.C1.V3` | 3-5 year rolling trend | M1 | `enrollment_rolling_3y_avg`, `enrollment_rolling_5y_avg` |
| `M1.C1.V4` | Growth/decline rate | M1 | `enrollment_growth_rate_pct` |
| `M1.C1.V5` | Department/program enrollment | M1 | `program_enrollment_count` |
| `M1.C1.V6` | Campus and regional enrollment | M1 | `campus_enrollment_count`, `region_enrollment_count` |
| `M1.C2` | Admissions funnel data | M1 | table: `data/ethiopia/admissions_funnel.parquet` |
| `M1.C2.V1` | Applications | M1 | `applications_count` |
| `M1.C2.V2` | Offers/admissions | M1 | `offers_count` |
| `M1.C2.V3` | Accepted offers | M1 | `accepted_offers_count` |
| `M1.C2.V4` | Yield rate | M1 | `yield_rate_pct` |
| `M1.C2.V5` | Applicants per seat | M1 | `applicants_per_seat` |
| `M1.C2.V6` | First-choice program demand | M1 | `first_choice_demand_count` |
| `M1.C3` | National entrance exam and placement data | M1 | table: `data/ethiopia/exam_placement.parquet` |
| `M1.C3.V1` | Entrance exam participation | M1 | `exam_candidates_count` |
| `M1.C3.V2` | Pass rate | M1 | `exam_pass_rate_pct` |
| `M1.C3.V3` | Score distribution | M1 | `exam_score_mean`, `exam_score_sd`, `exam_score_p25`, `exam_score_p50`, `exam_score_p75` |
| `M1.C3.V4` | Program cutoff | M1 | `program_cutoff_score` |
| `M1.C3.V5` | Placement decision | M1 | `placed_count`, `placement_rate_pct` |
| `M1.C3.V6` | Field allocation | M1 | `field_allocation_count`, `band_allocation_ratio` |
| `M1.C4` | Program capacity and quota policy | M1 | table: `data/ethiopia/capacity_quota.parquet` |
| `M1.C4.V1` | Approved intake quota | M1 | `approved_intake_quota` |
| `M1.C4.V2` | Available seats | M1 | `available_seats` |
| `M1.C4.V3` | Program capacity | M1 | `program_capacity` |
| `M1.C4.V4` | New program expansion | M1 | `program_expansion_flag` |
| `M1.C4.V5` | Program suspension/closure | M1 | `program_suspension_flag` |
| `M1.C4.V6` | Strategic priority field | M1 | `strategic_priority_flag` |
| `M1.C5` | Demographic pipeline | M1 | table: `data/ethiopia/demographics.parquet` |
| `M1.C5.V1` | High-school completers / exam candidates | M1 | `grade12_completers_count` |
| `M1.C5.V2` | University-age population | M1 | `university_age_population` |
| `M1.C5.V3` | Regional youth population | M1 | `regional_youth_population` |
| `M1.C5.V4` | Migration patterns | M1 | `net_internal_migration` |
| `M1.C6` | Cohort progression and retention | M1 | table: `data/ethiopia/cohort_progression.parquet` |
| `M1.C6.V1` | Retention rate | M1 | `retention_rate_pct` |
| `M1.C6.V2` | Dropout rate | M1 | `dropout_rate_pct` |
| `M1.C6.V3` | Transfer rate | M1 | `transfer_rate_pct` |
| `M1.C6.V4` | Completion rate | M1 | `completion_rate_pct` |
| `M1.C6.V5` | Time to graduation | M1 | `time_to_graduation_years` |
| `M1.C7` | Lagged employment outcomes by field | M1 | table: `data/ethiopia/graduate_outcomes.parquet` |
| `M1.C7.V1` | Graduate employment rate by field | M1 | `graduate_employment_rate_pct` |
| `M1.C7.V2` | Graduate unemployment rate | M1 | `graduate_unemployment_rate_pct` |
| `M1.C7.V3` | Median earnings where available | M1 | `median_earnings_etb` |
| `M1.C7.V4` | Vacancy demand by field | M1 | `vacancy_demand_by_field` |
| `M1.C7.V5` | Skills shortage signals | M1 | `skills_shortage_signal` |
| `M1.C8` | Institutional capacity and quality | M1 | table: `data/ethiopia/institution_capacity.parquet` |
| `M1.C8.V1` | Faculty-student ratio | M1 | `faculty_student_ratio` |
| `M1.C8.V2` | Laboratories | M1 | `laboratory_count` |
| `M1.C8.V3` | Classrooms | M1 | `classroom_count` |
| `M1.C8.V4` | Accreditation status | M1 | `accreditation_status` |
| `M1.C8.V5` | Program quality indicators | M1 | `program_quality_index` |
| `M1.C9` | Tuition, financial support and scholarships | M1 | table: `data/ethiopia/finance_support.parquet` |
| `M1.C9.V1` | Fees | M1 | `tuition_fee_etb` |
| `M1.C9.V2` | Stipends | M1 | `stipend_etb` |
| `M1.C9.V3` | Scholarships | M1 | `scholarship_availability` |
| `M1.C9.V4` | Loans and other financial incentives | M1 | `cost_sharing_loan_etb` |
| `M1.C10` | Macroeconomic and regional socio-economic conditions | M1 | table: `data/ethiopia/macro_regional.parquet` |
| `M1.C10.V1` | Inflation | M1 | `inflation_rate_pct` |
| `M1.C10.V2` | Household-income proxies | M1 | `household_income_proxy_etb` |
| `M1.C10.V3` | Youth unemployment | M1 | `youth_unemployment_rate_pct` |
| `M1.C10.V4` | Regional socio-economic indicators | M1 | `regional_socioeconomic_index` |
| `M2.C1` | Historical employment and unemployment trends | M2 | table: `data/ethiopia/labour_history.parquet` |
| `M2.C1.V1` | Employment level | M2 | `employment_level` |
| `M2.C1.V2` | Unemployment rate | M2 | `unemployment_rate_pct` |
| `M2.C1.V3` | Youth unemployment | M2 | `youth_unemployment_rate_pct` |
| `M2.C1.V4` | Sector employment | M2 | `sector_employment` |
| `M2.C1.V5` | Employment growth | M2 | `employment_growth_pct` |
| `M2.C1.V6` | Job creation | M2 | `job_creation_count` |
| `M2.C1.V7` | Labor-force participation | M2 | `labour_force_participation_pct` |
| `M2.C1.V8` | Lagged employment | M2 | `employment_lag_1y`, `employment_lag_2y` |
| `M2.C2` | Sector-level employment and economic output | M2 | table: `data/ethiopia/sector_output.parquet` |
| `M2.C2.V1` | Sector value-added | M2 | `sector_value_added_etb` |
| `M2.C2.V2` | Sector growth rate | M2 | `sector_growth_rate_pct` |
| `M2.C2.V3` | Production/output | M2 | `sector_output_index` |
| `M2.C2.V4` | Business formation | M2 | `business_formation_count` |
| `M2.C2.V5` | Investment | M2 | `sector_investment_etb` |
| `M2.C2.V6` | Employment intensity | M2 | `employment_intensity` |
| `M2.C3` | Formal versus informal sector structure | M2 | table: `data/ethiopia/formal_informal.parquet` |
| `M2.C3.V1` | Formal wage employment | M2 | `formal_wage_employment` |
| `M2.C3.V2` | Informal employment | M2 | `informal_employment` |
| `M2.C3.V3` | Self-employment | M2 | `self_employment` |
| `M2.C3.V4` | Underemployment | M2 | `underemployment` |
| `M2.C3.V5` | Microenterprise activity | M2 | `microenterprise_activity` |
| `M2.C3.V6` | Sector absorption patterns | M2 | `sector_absorption_rate` |
| `M2.C4` | Job vacancy and recruitment signals | M2 | table: `data/ethiopia/vacancies.parquet` |
| `M2.C4.V1` | Vacancy count | M2 | `vacancy_count` |
| `M2.C4.V2` | Job title/occupation | M2 | `occupation`, `occupation_frequency` |
| `M2.C4.V3` | Required education | M2 | `required_education` |
| `M2.C4.V4` | Required experience | M2 | `required_experience_years` |
| `M2.C4.V5` | Hiring trends | M2 | `hiring_trend_pct`, `time_to_fill_days` |
| `M2.C5` | Skills demand and shortage indicators | M2 | table: `data/ethiopia/skills_demand.parquet` |
| `M2.C5.V1` | Technical skills | M2 | `technical_skill_demand` |
| `M2.C5.V2` | Digital skills | M2 | `digital_skill_demand` |
| `M2.C5.V3` | Soft skills | M2 | `soft_skill_demand` |
| `M2.C5.V4` | Emerging skills | M2 | `emerging_skill_demand` |
| `M2.C5.V5` | Shortage indicator | M2 | `skill_shortage_index` |
| `M2.C5.V6` | Oversupply indicator | M2 | `skill_oversupply_index` |
| `M2.C6` | Public-sector hiring and government project pipeline | M2 | table: `data/ethiopia/public_hiring.parquet` |
| `M2.C6.V1` | Civil-service hiring plans | M2 | `civil_service_hiring_plan` |
| `M2.C6.V2` | Hiring freezes/expansions | M2 | `hiring_policy_state` |
| `M2.C6.V3` | Public projects | M2 | `public_project_count` |
| `M2.C6.V4` | Mega-project staffing demand | M2 | `megaproject_staffing_demand` |
| `M2.C7` | FDI and industrial development pipeline | M2 | table: `data/ethiopia/fdi_industrial.parquet` |
| `M2.C7.V1` | FDI inflows by sector/region | M2 | `fdi_inflow_usd` |
| `M2.C7.V2` | Industrial parks | M2 | `industrial_park`, `industrial_park_operational_flag` |
| `M2.C7.V3` | New investment projects | M2 | `new_investment_project_count` |
| `M2.C7.V4` | Factory expansion | M2 | `factory_expansion_count` |
| `M2.C7.V5` | Expected employment | M2 | `expected_employment` |
| `M2.C7.V6` | Private investment pipeline | M2 | `private_investment_pipeline_etb` |
| `M2.C8` | Macroeconomic and financial conditions | M2 | table: `data/ethiopia/macro_financial.parquet` |
| `M2.C8.V1` | GDP growth | M2 | `gdp_growth_rate_pct` |
| `M2.C8.V2` | Inflation / CPI | M2 | `cpi_index`, `inflation_rate_pct` |
| `M2.C8.V3` | Exchange rate | M2 | `exchange_rate_etb_usd` |
| `M2.C8.V4` | Forex availability | M2 | `forex_reserve_months` |
| `M2.C8.V5` | Investment levels | M2 | `gross_investment_etb` |
| `M2.C8.V6` | Interest conditions | M2 | `interest_rate_pct` |
| `M2.C9` | Labor-force demographics, migration and regional variation | M2 | table: `data/ethiopia/labour_demographics.parquet` |
| `M2.C9.V1` | Working-age population | M2 | `working_age_population` |
| `M2.C9.V2` | Education level | M2 | `education_level_distribution` |
| `M2.C9.V3` | Migration / brain drain | M2 | `skilled_emigration_count` |
| `M2.C9.V4` | Return migration | M2 | `return_migration_count` |
| `M2.C9.V5` | Regional labor absorption | M2 | `regional_absorption_rate` |
| `M2.C10` | Seasonality, commodity and external shocks | M2 | table: `data/ethiopia/shocks_seasonality.parquet` |
| `M2.C10.V1` | Agricultural cycles | M2 | `agricultural_season` |
| `M2.C10.V2` | Hiring cycles | M2 | `hiring_season_index` |
| `M2.C10.V3` | Commodity prices | M2 | `commodity_price_index` |
| `M2.C10.V4` | Major external shocks | M2 | `external_shock_flag` |

## DOC1 — procedure

| Id | Step | Satisfied by |
|---|---|---|
| `PROC.S1` | 1. Use literature review, the approved proposal and Ethiopia-specific domain knowledge to def | artefact: `docs/spec/model1_attributes.yaml`; also: `docs/spec/model2_attributes.yaml` |
| `PROC.S2` | 2. Validate attribute relevance with experts from higher education, the Ministry of Education | endpoint: `/api/methodology/expert-validations`; component: `frontend/src/pages/admin/AdminMethodologyPage.jsx` |
| `PROC.S3` | 3. Prioritize Tier 1 and Tier 2 variables for data collection because they are expected to ha | endpoint: `/api/methodology/priority-tiers`; artefact: `scripts/spec_report.py` |
| `PROC.S4` | 4. Train multiple models and compare predictive performance. | endpoint: `/api/methodology/model-comparison`; artefact: `ml/compare_models.py`; report: `docs/MODEL_COMPARISON.md` |
| `PROC.S5` | 5. Calculate empirical feature importance after training using model-based importance and SHA | endpoint: `/api/methodology/feature-importance`; artefact: `ml/explain_predictions.py`; report: `docs/FEATURE_IMPORTANCE.md` |
| `PROC.S6` | 6. Report the final data-driven feature rankings separately from the proposed expert/data-col | report: `docs/FEATURE_IMPORTANCE.md` |
| `PROC.S7` | 7. If fixed pre-training weights are required, explicitly add a separate AHP or hybrid AHP-ML | endpoint: `/api/ahp/weights`; component: `frontend/src/pages/admin/AdminMethodologyPage.jsx`; module: `ml/ahp/`; also: `/api/ahp/consistency` |

## DOC2 — widgets (44)

| Id | Widget | Role | Endpoint | Component |
|---|---|---|---|---|
| `W.STU.01` | Profile and academic eligibility | STUDENT | `/api/student/profile` | `frontend/src/pages/student/ProfilePage.jsx` |
| `W.STU.02` | Future labor-market outlook | STUDENT | `/api/student/labour-outlook` | `frontend/src/pages/student/LabourOutlookPage.jsx` |
| `W.STU.03` | Student demand vs market demand | STUDENT | `/api/student/demand-comparison` | `frontend/src/pages/student/DemandComparisonPage.jsx` |
| `W.STU.04` | Field opportunity and alignment | STUDENT | `/api/student/field-alignment` | `frontend/src/pages/student/FieldAlignmentPage.jsx` |
| `W.STU.05` | Graduate supply-demand gap | STUDENT | `/api/student/supply-demand-gap` | `frontend/src/pages/student/SupplyDemandGapPage.jsx` |
| `W.STU.06` | Alternative field recommendations | STUDENT | `/api/student/alternatives` | `frontend/src/pages/EscapeRoutePage.jsx` |
| `W.STU.07` | Skill-gap recommendations | STUDENT | `/api/student/skill-gaps` | `frontend/src/pages/SkillRoadmapPage.jsx` |
| `W.STU.08` | Program-to-occupation pathways | STUDENT | `/api/student/pathways` | `frontend/src/pages/student/PathwayMapPage.jsx` |
| `W.STU.09` | Opportunities and alerts | STUDENT | `/api/student/opportunities` | `frontend/src/pages/student/OpportunitiesPage.jsx` |
| `W.UNI.01` | Enrollment and capacity summary | UNIVERSITY | `/api/institution/me` | `frontend/src/pages/university/InstitutionOverviewPage.jsx` |
| `W.UNI.02` | Unconstrained student demand forecast | UNIVERSITY | `/api/model1/demand/unconstrained` | `frontend/src/pages/university/DemandForecastPage.jsx` |
| `W.UNI.03` | Policy-constrained enrollment forecast | UNIVERSITY | `/api/model1/demand/constrained` | `frontend/src/pages/university/ConstrainedForecastPage.jsx` |
| `W.UNI.04` | Program demand vs labor demand | UNIVERSITY | `/api/institution/demand-vs-labour` | `frontend/src/pages/university/ThreeWayComparisonPage.jsx` |
| `W.UNI.05` | Program health and alignment flags | UNIVERSITY | `/api/institution/program-health` | `frontend/src/pages/university/ProgramPortfolioPage.jsx` |
| `W.UNI.06` | Application and placement funnel | UNIVERSITY | `/api/institution/funnel` | `frontend/src/pages/university/FunnelPage.jsx` |
| `W.UNI.07` | Cohort progression | UNIVERSITY | `/api/institution/cohort-progression` | `frontend/src/pages/university/CohortProgressionPage.jsx` |
| `W.UNI.08` | Graduate outcome feedback | UNIVERSITY | `/api/institution/graduate-outcomes` | `frontend/src/pages/university/GraduateOutcomesPage.jsx` |
| `W.UNI.09` | Resource and quota planning | UNIVERSITY | `/api/institution/resource-planning` | `frontend/src/pages/university/ResourceEfficiencyPage.jsx` |
| `W.UNI.10` | Curriculum and skills alignment | UNIVERSITY | `/api/institution/curriculum-alignment` | `frontend/src/pages/university/CurriculumAlignmentPage.jsx` |
| `W.MOE.01` | National education and demand overview | MOE | `/api/education/overview` | `frontend/src/pages/moe/EducationOverviewPage.jsx` |
| `W.MOE.02` | Unconstrained vs constrained demand | MOE | `/api/education/demand-constrained-comparison` | `frontend/src/pages/moe/ConstraintComparisonPage.jsx` |
| `W.MOE.03` | National field supply-demand gap | MOE | `/api/education/supply-demand-gap` | `frontend/src/pages/moe/NationalGapPage.jsx` |
| `W.MOE.04` | Quota and placement policy simulator | MOE | `/api/education/policy-simulator` | `frontend/src/pages/moe/PolicySimulatorPage.jsx` |
| `W.MOE.05` | Strategic field prioritization | MOE | `/api/model3/policy-priority` | `frontend/src/pages/moe/InvestmentPriorityPage.jsx` |
| `W.MOE.06` | Regional education-labor alignment | MOE | `/api/education/regional-alignment` | `frontend/src/pages/moe/RegionalAlignmentPage.jsx` |
| `W.MOE.07` | Institution comparison | MOE | `/api/education/institution-comparison` | `frontend/src/pages/moe/InstitutionComparisonPage.jsx` |
| `W.MOE.08` | Policy impact monitoring | MOE | `/api/education/policy-impact` | `frontend/src/pages/moe/PolicyImpactPage.jsx` |
| `W.MOL.01` | Labor-market overview | MOL | `/api/labour/overview` | `frontend/src/pages/mol/LabourOverviewPage.jsx` |
| `W.MOL.02` | Formal vs informal absorption | MOL | `/api/model2/formal-informal` | `frontend/src/pages/mol/FormalInformalPage.jsx` |
| `W.MOL.03` | Sector and occupational demand forecast | MOL | `/api/model2/forecast` | `frontend/src/pages/mol/SectorForecastPage.jsx` |
| `W.MOL.04` | Skills demand and shortage heatmap | MOL | `/api/model2/skills-shortage` | `frontend/src/pages/mol/SkillsMismatchPage.jsx` |
| `W.MOL.05` | Public-sector hiring pipeline | MOL | `/api/model2/public-pipeline` | `frontend/src/pages/mol/PublicHiringPage.jsx` |
| `W.MOL.06` | FDI and industrial development pipeline | MOL | `/api/model2/fdi-pipeline` | `frontend/src/pages/mol/FdiPipelinePage.jsx` |
| `W.MOL.07` | Graduate absorption and transition | MOL | `/api/labour/graduate-absorption` | `frontend/src/pages/mol/GraduateAbsorptionPage.jsx` |
| `W.MOL.08` | Migration and labor supply pressure | MOL | `/api/model2/migration` | `frontend/src/pages/mol/MigrationPage.jsx` |
| `W.MOL.09` | Workforce planning report | MOL | `/api/labour/workforce-report` | `frontend/src/pages/mol/WorkforceReportPage.jsx` |
| `W.ADM.01` | Platform health | ADMIN | `/api/admin/platform-health` | `frontend/src/pages/admin/AdminOverviewPage.jsx` |
| `W.ADM.02` | Data pipeline monitor | ADMIN | `/api/admin/pipeline-status` | `frontend/src/pages/admin/AdminPipelinePage.jsx` |
| `W.ADM.03` | Model performance monitor | ADMIN | `/api/monitoring/drift` | `frontend/src/pages/admin/AdminMonitoringPage.jsx` |
| `W.ADM.04` | Feature importance and explainability | ADMIN | `/api/methodology/feature-importance` | `frontend/src/pages/admin/AdminMethodologyPage.jsx` |
| `W.ADM.05` | Scenario governance | ADMIN | `/api/admin/scenarios` | `frontend/src/pages/admin/AdminScenariosPage.jsx` |
| `W.ADM.06` | Data quality and anomaly flags | ADMIN | `/api/admin/data-quality` | `frontend/src/pages/admin/AdminDataQualityPage.jsx` |
| `W.ADM.07` | User and role management | ADMIN | `/api/users` | `frontend/src/pages/admin/AdminUsersPage.jsx` |
| `W.ADM.08` | Audit log | ADMIN | `/api/admin/audit-log` | `frontend/src/pages/admin/AdminAuditLogPage.jsx` |

## Waivers (caveats, not missing widgets)

| Id | Caveat | Retires when |
|---|---|---|
| `WV.US1` | Placement XGBoost, salary XGBoost, US LSTM enrolment and Prophet demand artefacts remain on disk and on leftover tool routes (/student/evaluator, /student/salary, /student/market, /university/enrollment). They are not Ethiopia Model 1 or Model 2 scores. Wave 9 hid those links from role nav; bookmarked URLs still work. | Those tool routes are removed or the artefacts are retrained on Ethiopia fact tables and labelled as such. |
| `WV.SIM1` | Every Ethiopia figure is provenance.tier simulated until official CSA, MoE or ESS files replace the parquets under docs/spec/ingestion/. | An official file is ingested for a table and that series is restamped tier official. |
| `WV.OLS1` | M1/M2 ols_lags chronological holdout RMSE is near-zero on the simulated lag construction. Comparison still includes seasonal-naive and historical-mean. Figures are not ministry accuracy. | Holdout RMSE is recomputed on official series that are not generated from the same lags. |

## What we did not do

- Official CSA / MoE / ESS replacement files. Every Ethiopia figure stays `tier: simulated`.
- Training with AHP or `collection_priority`. SHAP and AHP stay in separate panels.
- Replacing `education_service.get_investment_priority` into W.MOE.05. The yaml ranker stays on its own route; the page uses policy-priority.
- Deleting leftover US tool routes. Wave 9 hid them from role nav; artefacts stay on disk (WV.US1).
- Dark mode.
- Ensemble stacking rebuild.
- Real 5 / 10 / 20 % admission-risk thresholds.
- Tagging `v1.0.0` (not in this wave unless asked).
- Recording the walkthrough video. The click script is [WALKTHROUGH.md](WALKTHROUGH.md).

## Verification

```text
python scripts/spec_report.py
pytest tests/test_spec_coverage.py -m "integrity or honesty or coverage"
pytest tests/test_honesty_live.py tests/test_scopes.py tests/test_ahp.py tests/test_constraints.py
cd frontend && npm test
```

No Playwright / browser MCP in this environment (same as Wave 7). Substitute:
live API matrix in `tests/test_honesty_live.py` and `tests/test_scopes.py` plus
Vitest. Record the five-role video from [WALKTHROUGH.md](WALKTHROUGH.md).
