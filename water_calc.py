from collections import OrderedDict
import pulp

# salts
GYPSUM = "GYPSUM"
CALCIUM_CHLORIDE = "CALCIUM_CHLORIDE"
EPSOM = "EPSOM"
CHALK = "CHALK"
TABLE_SALT = "TABLE_SALT"

# Ions
CA = "CA"
MG = "MG"
NA = "NA"
CL = "CL"
SO4 = "SO4"
HCO3 = "HCO3"

ALL_IONS = [
  CA,
  MG,
  NA,
  CL,
  SO4,
  HCO3
]

BREWING_SALTS = [GYPSUM, CALCIUM_CHLORIDE, EPSOM, CHALK, TABLE_SALT]

class WaterProfile:
  name = ""
  ions_ppm = None
  ph = 0

  def __init__(self, name, **kwargs):
    self.name = name
    self.ions_ppm = {}
    for ION in ALL_IONS:
      self.ions_ppm[ION] = kwargs.get(ION, 0)
    self.ph = kwargs.get('ph', 7)

  def __sub__(self, other):
    return WaterProfile(
      "{0} - {1}".format(self.name, other.name),
      ca_ppm=self.ca_ppm - other.ca_ppm,
      mg_ppm=self.mg_ppm - other.mg_ppm,
      na_ppm=self.na_ppm - other.na_ppm,
      so4_ppm=self.so4_ppm - other.so4_ppm,
      hco3_ppm=self.hco3_ppm - other.hco3_ppm,
      ph=other.ph
    )

  def get_ion_ppm(self, ion):
    return self.ions_ppm[ion]

  def get_ions_in_liters(self, liters):
    ions_mgl = {}
    for ion in ALL_IONS:
      ions_mgl[ion] = self.get_ion_ppm(ion) * liters
    return ions_mgl

  def __str__(self):
    ions_strs = []
    for ion in ALL_IONS:
      ions_strs.append("{0}: {1}".format(ion, self.get_ion_ppm(ion)))
    return "{0} Profile: {1}".format(self.name, ', '.join(ions_strs))


class SaltAddition:
  name = ""
  ion_percents = None
  weight = 0

  def __init__(self, name, **kwargs):
    self.name = name
    self.weight = kwargs.get('weight', 0)
    self.ion_percents = OrderedDict()
    for ion in ALL_IONS:
      self.ion_percents[ion] = kwargs.get(ion, 0)
    self.ion_percents = dict(sorted(self.ion_percents.items(), key=lambda item: item[1], reverse=True))

  def get_ions(self):
    ions = []
    for ion in self.ion_percents.keys():
      if self.ion_percents[ion] > 0:
        ions.append(ion)
    return ions

class WaterCalc:
  # volume in liters
  volume_l = 0
  source_profile = None
  target_profile = None
  current_ion_mgs = {}

  def __init__(self, volume_l, source_profile, target_profile):
    self.volume_l = volume_l
    self.source_profile = source_profile
    self.target_profile = target_profile
    self.current_ion_mgs = source_profile.get_ions_in_liters(volume_l)

  def get_ions_as_ppm(self):
    ions_ppm = {}
    for ion in ALL_IONS:
      ions_ppm[ion] = self.current_ion_mgs[ion]/self.volume_l
    return ions_ppm

  def cut_with_distilled_water(self, distilled_l):
    ion_mgl = self.get_ions_as_ppm()
    source_water_volume = self.volume_l - distilled_l

    print("Previous ion ppms")
    print(ion_mgl)
    for ion in ALL_IONS:
      ion_mgs_in_source_water = ion_mgl[ion] * source_water_volume
      # new_ion_mgl = ion_mgs_in_source_water / (source_water_volume + distilled_l)
      self.current_ion_mgs[ion] = ion_mgs_in_source_water

    print("New ion ppms")
    print(self.get_ions_as_ppm())

  def get_sorted_difference_to_target(self):
    target_ions_mgl = self.target_profile.get_ions_in_liters(self.volume_l)

    differences = {}
    for ion in ALL_IONS:
      difference = target_ions_mgl[ion] - self.current_ion_mgs[ion]
      differences[ion] = difference

    return dict(sorted(differences.items(), key=lambda item: item[1], reverse=True))

  def __str__(self):
    leader = ""
    output = ""
    output += leader + "Ion PPMs: "

    ion_ppms = self.get_ions_as_ppm()
    ion_ppm_strs = []
    for ion in ALL_IONS:
      ion_ppm_strs.append("{0}: {1}".format(ion, ion_ppms[ion]))

    output += ', '.join(ion_ppm_strs)
    return output

def gallons_to_liters(gallons):
  return gallons*3.785

SOURCE_WATER = WaterProfile("Source Water", CA=1, MG=0, NA=5, CL=3, SO4=0, HCO3=3, ph=8)
# TARGET_WATER = WaterProfile("Bavarian Water", CA=22, MG=8, NA=0, CL=39, SO4=31, HCO3=0, ph=8)
# TARGET_WATER = WaterProfile("Bavarian Water", CA=22, MG=8, NA=5, CL=39, SO4=31, HCO3=3, ph=8)
TARGET_WATER = WaterProfile("Festbier Water", CA=48, MG=10, NA=7, CL=44, SO4=35, HCO3=3, ph=8)

GYPSUM = SaltAddition(GYPSUM, weight=172, CA=0.23, SO4=0.56)
CALCIUM_CHLORIDE = SaltAddition(CALCIUM_CHLORIDE, weight=146, CA=0.27, CL=0.48)
EPSOM = SaltAddition(EPSOM, weight=246, MG=0.1, SO4=0.39)
CHALK = SaltAddition(CHALK, weight=100, CA=0.40, HCO3=0.60)
TABLE_SALT = SaltAddition(TABLE_SALT, weight=58, NA=0.40, CL=0.60)

def linear_programming_solver(water_calc, acceptable_error_ppm = 5, retries = 5):
  ion_differences = water_calc.get_sorted_difference_to_target()
  prob = pulp.LpProblem("BrewingWater", pulp.LpMinimize)

  def get_acceptable_min(ion):
    if ion_differences[ion] - acceptable_error_ppm*water_calc.volume_l < 0:
      return 0
    else:
      return ion_differences[ion] - acceptable_error_ppm*water_calc.volume_l

  def get_acceptable_max(ion):
    return ion_differences[ion] + acceptable_error_ppm*water_calc.volume_l

  gypsum = pulp.LpVariable("Gypsum", 0, 10000, pulp.LpInteger)
  cacl = pulp.LpVariable("CalciumChloride", 0, 10000, pulp.LpInteger)
  epsom = pulp.LpVariable("Epsom", 0, 10000, pulp.LpInteger)
  chalk = pulp.LpVariable("Chalk", 0, 10000, pulp.LpInteger)
  table_salt = pulp.LpVariable("TableSalt", 0, 10000, pulp.LpInteger)

  salts = [gypsum, cacl, epsom, chalk, table_salt]

  ca = pulp.LpVariable("CA", None, None)
  so4 = pulp.LpVariable("SO4", None, None)
  cl = pulp.LpVariable("CL", None, None)
  mg = pulp.LpVariable("MG", None, None)
  hco3 = pulp.LpVariable("HCO3", None, None)
  na = pulp.LpVariable("NA", None, None)

  ions = [ca, so4, cl, mg, hco3, na]

  deviations = {}
  for var in ions:
    var_neg = pulp.LpVariable('{0}_neg'.format(var.name), lowBound=0)
    var_pos = pulp.LpVariable('{0}_pos'.format(var.name), lowBound=0)
    deviations[var.name] = (var_pos, var_neg)

  # objective: minimize deviation
  prob += pulp.lpSum(dev for pair in deviations.values() for dev in pair)
  # prob += gypsum + cacl + epsom + chalk + table_salt, 'Total Salt Weight'

  # Add constraints for the var_neg and var_pos values to subtract to var
  for ion in ions:
    prob += ion == deviations[ion.name][0] - deviations[ion.name][1], '{0}_abs'.format(ion.name)

  # Calcium rules
  prob += ca == gypsum * GYPSUM.ion_percents[CA] + cacl * CALCIUM_CHLORIDE.ion_percents[CA] + chalk * CHALK.ion_percents[CA], 'ca_def'
  prob += ca >= get_acceptable_min(CA), 'ca_min'
  prob += ca <= get_acceptable_max(CA), 'ca_max'

  # Chlorine
  prob += cl == cacl * CALCIUM_CHLORIDE.ion_percents[CL] + table_salt * TABLE_SALT.ion_percents[CL], 'cl_def'
  prob += cl >= get_acceptable_min(CL), 'cl_min'
  prob += cl <= get_acceptable_max(CL), 'cl_max'

  # SO4
  prob += so4 == gypsum * GYPSUM.ion_percents[SO4] + epsom * EPSOM.ion_percents[SO4], 'so4_def'
  prob += so4 >= get_acceptable_min(SO4), 'so4_min'
  prob += so4 <= get_acceptable_max(SO4), 'so4_max'

  # MG
  prob += mg == epsom * EPSOM.ion_percents[MG], 'mg_def'
  prob += mg >= get_acceptable_min(MG), 'mg_min'
  prob += mg <= get_acceptable_max(MG), 'mg_max'

  # HCO3
  prob += hco3 == chalk * CHALK.ion_percents[HCO3], 'hco3_def'
  prob += hco3 >= get_acceptable_min(HCO3), 'hco3_min'
  prob += hco3 <= get_acceptable_max(HCO3), 'hco3_max'

  # NA
  prob += na == table_salt * TABLE_SALT.ion_percents[NA], 'na_def'
  prob += na >= get_acceptable_min(NA), 'na_min'
  prob += na <= get_acceptable_max(NA), 'na_max'

  prob.writeLP("BrewingWater.lp")

  prob.solve(pulp.PULP_CBC_CMD(msg=False))


  if prob.sol_status == -1:
    if retries > 0:
      new_error_margin = acceptable_error_ppm*2
      print('Solution not found with error margin of {0} ppm, retrying with acceptable error margin of {1} ppm'.format(acceptable_error_ppm, new_error_margin))
      linear_programming_solver(water_calc, new_error_margin, retries - 1)
    else:
      print('Solution not found')
  else:
    vars = prob.variablesDict()

    print('Solution found with acceptable error of {0} ppm'.format(acceptable_error_ppm))
    print('Solution Water Profile')
    for ion in ions:
      print("- {0}: {1} (ppm delta: {2})".format(ion.name, vars[ion.name].varValue/water_calc.volume_l, ion_differences[ion.name]/water_calc.volume_l - vars[ion.name].varValue/water_calc.volume_l))

    print('')
    print('Add the following salts:')
    for salt in salts:
      salt_weight_g = round(vars[salt.name].varValue/1000, 1)
      if salt_weight_g > 0:
        print("- {0}: {1} g".format(salt.name, salt_weight_g))

def main():
  # calc_brewing_salts(SOURCE_WATER, TARGET_WATER, 6.75)
  water_calc = WaterCalc(gallons_to_liters( 6.75), SOURCE_WATER, TARGET_WATER)
  linear_programming_solver(water_calc)


main()
