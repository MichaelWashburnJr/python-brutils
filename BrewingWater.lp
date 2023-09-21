\* BrewingWater *\
Minimize
OBJ: CA_neg + CA_pos + CL_neg + CL_pos + HCO3_neg + HCO3_pos + MG_neg + MG_pos
 + NA_neg + NA_pos + SO4_neg + SO4_pos
Subject To
CA_abs: CA + CA_neg - CA_pos = 0
CL_abs: CL + CL_neg - CL_pos = 0
HCO3_abs: HCO3 + HCO3_neg - HCO3_pos = 0
MG_abs: MG + MG_neg - MG_pos = 0
NA_abs: NA + NA_neg - NA_pos = 0
SO4_abs: SO4 + SO4_neg - SO4_pos = 0
ca_def: CA - 0.27 CalciumChloride - 0.4 Chalk - 0.23 Gypsum = 0
ca_max: CA <= 1456.27875
ca_min: CA >= 945.30375
cl_def: CL - 0.48 CalciumChloride - 0.6 TableSalt = 0
cl_max: CL <= 1302.98625
cl_min: CL >= 792.01125
hco3_def: - 0.6 Chalk + HCO3 = 0
hco3_max: HCO3 <= 255.4875
hco3_min: HCO3 >= 0
mg_def: - 0.1 Epsom + MG = 0
mg_max: MG <= 510.975
mg_min: MG >= 0
na_def: NA - 0.4 TableSalt = 0
na_max: NA <= 306.585
na_min: NA >= 0
so4_def: - 0.39 Epsom - 0.56 Gypsum + SO4 = 0
so4_max: SO4 <= 1149.69375
so4_min: SO4 >= 638.71875
Bounds
 CA free
 CL free
 0 <= CalciumChloride <= 10000
 0 <= Chalk <= 10000
 0 <= Epsom <= 10000
 0 <= Gypsum <= 10000
 HCO3 free
 MG free
 NA free
 SO4 free
 0 <= TableSalt <= 10000
Generals
CalciumChloride
Chalk
Epsom
Gypsum
TableSalt
End
