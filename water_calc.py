import itertools
from collections import OrderedDict
import functools
import bisect
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
  salts_added_mg = {}
  is_solution = False

  def __init__(self, volume_l, source_profile, target_profile):
    self.volume_l = volume_l
    self.source_profile = source_profile
    self.target_profile = target_profile
    self.is_solution = False

    self.current_ion_mgs = source_profile.get_ions_in_liters(volume_l)

  def clone(self):
    new_calc = WaterCalc(self.volume_l, self.source_profile, self.target_profile)
    new_calc.current_ion_mgs = dict(self.current_ion_mgs)
    new_calc.salts_added_mg = dict(self.salts_added_mg)
    return new_calc

  def add_salt(self, salt_addition, mass_mg):
      if salt_addition.name not in self.salts_added_mg:
        self.salts_added_mg[salt_addition.name] = 0
      self.salts_added_mg[salt_addition.name] = self.salts_added_mg[salt_addition.name] + mass_mg

      for ion in ALL_IONS:
        percent_of_ion = salt_addition.ion_percents[ion]
        self.current_ion_mgs[ion] += percent_of_ion * mass_mg
      return self

  def get_ions_as_ppm(self):
    ions_ppm = {}
    for ion in ALL_IONS:
      ions_ppm[ion] = self.current_ion_mgs[ion]/self.volume_l
    return ions_ppm

  def get_sorted_difference_to_target(self):
    target_ions_mgl = self.target_profile.get_ions_in_liters(self.volume_l)

    differences = {}
    for ion in ALL_IONS:
      difference = target_ions_mgl[ion] - self.current_ion_mgs[ion]
      differences[ion] = difference

    return dict(sorted(differences.items(), key=lambda item: item[1], reverse=True))

  def get_total_error_margin(self):
    target_ions_mgl = self.target_profile.get_ions_in_liters(self.volume_l)

    differences = {}
    for ion in ALL_IONS:
      difference = target_ions_mgl[ion] - self.current_ion_mgs[ion]
      differences[ion] = difference

    # differences = self.get_sorted_difference_to_target()
    error_margin = 0
    for ion in ALL_IONS:
      error_margin += differences[ion]

    print('Error Margin!')
    print(error_margin)
    return error_margin

  def __str__(self):
    leader = ""
    output = ""
    output += leader + "Ion PPMs: "

    ion_ppms = self.get_ions_as_ppm()
    ion_ppm_strs = []
    for ion in ALL_IONS:
      ion_ppm_strs.append("{0}: {1}".format(ion, ion_ppms[ion]))

    output += ', '.join(ion_ppm_strs)

    output += "\n" + leader + "Salt Additions: "
    salt_strs = []
    for salt in self.salts_added_mg.keys():
      salt_strs.append("{0}: {1} mg".format(salt, self.salts_added_mg[salt]))
    output += ', '.join(salt_strs)
    return output
  # def add_max_salt(self, salt_addition):
  #   pass

@functools.total_ordering
class Node:
  current_calc = None
  parent_node = None
  child_nodes = None

  def __init__(self, water_calc, parent_node = None):
    self.child_nodes = []
    self.current_calc = water_calc
    self.parent_node = parent_node

  def create_node_and_add_salt(self, salt_addition, mass_mg):
    new_calc = self.current_calc.clone()
    new_calc.add_salt(salt_addition, mass_mg)
    new_node = Node(new_calc, self)
    self.child_nodes.append(new_node)
    return new_node

  def get_error_margin(self):
    return self.current_calc.get_total_error_margin()

  def create_children(self, salt_additions, mass_mg):
    new_nodes = []
    for salt_addition in salt_additions:
      new_nodes.append(self.create_node_and_add_salt(salt_addition, mass_mg))
    return new_nodes

  def __eq__(self, other):
    return self.get_error_margin() == other.get_error_margin()

  def __lt__(self, other):
    return self.get_error_margin() < other.get_error_margin()

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

ALL_SALT_ADDITIONS = [GYPSUM, CALCIUM_CHLORIDE, EPSOM, CHALK, TABLE_SALT]

def find_solutions(original_node, step_mg=1000):
  cur_nodes = [original_node]
  cur_step_mg = step_mg

  while len(cur_nodes) > 0:
    cur_node = cur_nodes[0]
    cur_node_error_margin = cur_node.get_error_margin()
    cur_node.create_children(ALL_SALT_ADDITIONS, cur_step_mg)

    better_solutions = []
    for child in cur_node.child_nodes:
      if child.get_error_margin() < cur_node_error_margin:
        better_solutions.append(child)
    if len(better_solutions) > 0:
      cur_nodes.extend(better_solutions)
      cur_nodes.pop(0)
    elif cur_step_mg > 100:
      cur_step_mg = cur_step_mg / 2.0
    else:
      cur_nodes.pop(0)

def maybe_insert_new_top_10(solution_nodes, node):
  if len(solution_nodes) == 0:
    return [node]
  bisect.insort(solution_nodes, node)
  return solution_nodes[0:9]

def get_top_n_solutions(node):
  top_solutions = []

  lowest_top_solution = None
  cur_nodes = [node]
  while len(cur_nodes) > 0:
    cur_node = cur_nodes.pop(0)
    if len(top_solutions) < 10 or cur_node.get_error_margin() < lowest_top_solution or lowest_top_solution is None:
      top_solutions = maybe_insert_new_top_10(top_solutions, cur_node)

    lowest_top_solution = top_solutions[-1].get_error_margin()
    cur_nodes.extend(cur_node.child_nodes)

  return top_solutions

def calc_brewing_salts(source, target, gallons):
  print(source)
  print(target)
  water_calc = WaterCalc(gallons_to_liters(gallons), source, target)
  original_node = Node(water_calc)
  find_solutions(original_node)
  n = 1

  for solution in get_top_n_solutions(original_node):
    print('Solution {0}'.format(n))
    n += 1
    print('Error Margin: {0}'.format(solution.get_error_margin()))
    print('{0}'.format(solution.current_calc))
    print('')

  # print(water_calc.get_sorted_difference_to_target())
  # print(water_calc.get_ions_as_ppm())
  # salt_order_combos = list(itertools.permutations(BREWING_SALTS, len(BREWING_SALTS)))
  # print(salt_order_combos)

# GYPSUM = "GYPSUM"
# CALCIUM_CHLORIDE = "CALCIUM_CHLORIDE"
# EPSOM = "EPSOM"
# CHALK = "CHALK"
# TABLE_SALT = "TABLE_SALT"
# GYPSUM = SaltAddition(GYPSUM, weight=172, CA=0.23, SO4=0.56)
# CALCIUM_CHLORIDE = SaltAddition(CALCIUM_CHLORIDE, weight=146, CA=0.27, CL=0.48)
# EPSOM = SaltAddition(EPSOM, weight=246, MG=0.1, SO4=0.39)
# CHALK = SaltAddition(CHALK, weight=100, CA=0.40, HCO3=0.60)
# TABLE_SALT = SaltAddition(TABLE_SALT, weight=58, NA=0.40, CL=0.60)

def linear_programming_solver(source, target, gallons):
  prob = pulp.LpProblem("BrewingWater", pulp.LpMinimize)
  water_calc = WaterCalc(gallons_to_liters(gallons), source, target)
  ion_differences = water_calc.get_sorted_difference_to_target()
  ACCEPTABLE_ERROR = 10

  def get_acceptable_min(ion):
    if ion_differences[ion] - ACCEPTABLE_ERROR < 0:
      return 0
    else:
      return ion_differences[ion] - ACCEPTABLE_ERROR

  print(ion_differences)
  gypsum = pulp.LpVariable("Gypsum", 0, 10000, pulp.LpInteger)
  cacl = pulp.LpVariable("CalciumChloride", 0, 10000, pulp.LpInteger)
  epsom = pulp.LpVariable("Epsom", 0, 10000, pulp.LpInteger)
  chalk = pulp.LpVariable("Chalk", 0, 10000, pulp.LpInteger)
  table_salt = pulp.LpVariable("TableSalt", 0, 10000, pulp.LpInteger)

  # minimize salt weight
  prob += gypsum + cacl + epsom + chalk + table_salt, 'Total Salt Weight'

  # constraints
  # Calcium
  prob += gypsum * GYPSUM.ion_percents[CA] + cacl * CALCIUM_CHLORIDE.ion_percents[CA] + chalk * CHALK.ion_percents[CA] >= get_acceptable_min(CA), "ca_min"
  prob += gypsum * GYPSUM.ion_percents[CA] + cacl * CALCIUM_CHLORIDE.ion_percents[CA] + chalk * CHALK.ion_percents[CA] <= ion_differences[CA] + ACCEPTABLE_ERROR, "ca_max"
  # Chlorine
  prob += cacl * CALCIUM_CHLORIDE.ion_percents[CL] + table_salt * TABLE_SALT.ion_percents[CL] >= get_acceptable_min(CL), "cl_min"
  prob += cacl * CALCIUM_CHLORIDE.ion_percents[CL] + table_salt * TABLE_SALT.ion_percents[CL] <= ion_differences[CL] + ACCEPTABLE_ERROR, "cl_max"
  # SO4
  prob += gypsum * GYPSUM.ion_percents[SO4] + epsom * EPSOM.ion_percents[SO4] >= get_acceptable_min(SO4), "so4_min"
  prob += gypsum * GYPSUM.ion_percents[SO4] + epsom * EPSOM.ion_percents[SO4] <= ion_differences[SO4] + ACCEPTABLE_ERROR, "so4_max"
  # MG
  prob += epsom * EPSOM.ion_percents[MG] >= get_acceptable_min(MG), "mg_min"
  prob += epsom * EPSOM.ion_percents[MG] <= ion_differences[MG] + ACCEPTABLE_ERROR, "mg_max"
  # HCO3
  prob += chalk * CHALK.ion_percents[HCO3] >= get_acceptable_min(HCO3), "hco3_min"
  prob += chalk * CHALK.ion_percents[HCO3] <= ion_differences[HCO3] + ACCEPTABLE_ERROR, "hco3_max"
  # NA
  prob += table_salt * TABLE_SALT.ion_percents[NA] >= get_acceptable_min(NA), "na_min"
  prob += table_salt * TABLE_SALT.ion_percents[NA] <= ion_differences[NA] + ACCEPTABLE_ERROR, "na_max"

  prob.writeLP("BrewingWater.lp")

  prob.solve()

  for v in prob.variables():
    print(v.name, "=", v.varValue)



def main():
  # calc_brewing_salts(SOURCE_WATER, TARGET_WATER, 6.75)
  linear_programming_solver(SOURCE_WATER, TARGET_WATER, 6.75)

main()
