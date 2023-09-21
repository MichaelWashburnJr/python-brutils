\* BrewingWater *\
Minimize
Total_Salt_Weight: CalciumChloride + Chalk + Epsom + Gypsum + TableSalt
Subject To
ca_max: 0.27 CalciumChloride + 0.4 Chalk + 0.23 Gypsum <= 1210.79125
ca_min: 0.27 CalciumChloride + 0.4 Chalk + 0.23 Gypsum >= 1190.79125
cl_max: 0.48 CalciumChloride + 0.6 TableSalt <= 1057.49875
cl_min: 0.48 CalciumChloride + 0.6 TableSalt >= 1037.49875
hco3_max: 0.6 Chalk <= 10
hco3_min: 0.6 Chalk >= 0
mg_max: 0.1 Epsom <= 265.4875
mg_min: 0.1 Epsom >= 245.4875
na_max: 0.4 TableSalt <= 61.0975
na_min: 0.4 TableSalt >= 41.0975
so4_max: 0.39 Epsom + 0.56 Gypsum <= 904.20625
so4_min: 0.39 Epsom + 0.56 Gypsum >= 884.20625
Bounds
 0 <= CalciumChloride <= 10000
 0 <= Chalk <= 10000
 0 <= Epsom <= 10000
 0 <= Gypsum <= 10000
 0 <= TableSalt <= 10000
Generals
CalciumChloride
Chalk
Epsom
Gypsum
TableSalt
End
