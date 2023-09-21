\* BrewingWater *\
Minimize
Total_Salt_Weight: CalciumChloride + Chalk + Epsom + Gypsum + TableSalt
Subject To
MaximumCA: 0.27 CalciumChloride + 0.4 Chalk + 0.23 Gypsum <= 1300.79125
MaximumCl: 0.48 CalciumChloride + 0.6 TableSalt <= 1147.49875
MaximumHCO3: 0.6 Chalk <= 100
MaximumMG: 0.1 Epsom <= 355.4875
MaximumNA: 0.4 TableSalt <= 151.0975
MaximumSO4: 0.39 Epsom + 0.56 Gypsum <= 994.20625
MinimumCA: 0.27 CalciumChloride + 0.4 Chalk + 0.23 Gypsum >= 1100.79125
MinimumCL: 0.48 CalciumChloride + 0.6 TableSalt >= 947.49875
MinimumHCO3: 0.6 Chalk >= 0
MinimumMG: 0.1 Epsom >= 155.4875
MinimumNA: 0.4 TableSalt >= 0
MinimumSO4: 0.39 Epsom + 0.56 Gypsum >= 794.20625
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
