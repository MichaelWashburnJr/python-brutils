
class Fermentable:
  def __init__(self, name, extract_potential_gu, percent_in_recipe, is_extract = False):
    self.name = name
    self.extract_potential_gu = extract_potential_gu
    self.percent_in_recipe = percent_in_recipe
    self.lbs_in_recipe = None
    self.is_extract = is_extract

def get_fermentables_amount(final_gravity_gu, final_volume_g, fermentables, extract_efficiency_percent):
  total_gus = get_total_required_gravity_units(final_gravity_gu, final_volume_g)
  print(total_gus)
  for fermentable in fermentables:
    print(fermentable.percent_in_recipe)
    ingredient_extract = fermentable.percent_in_recipe * total_gus
    gravity_per_lb = extract_efficiency_percent * fermentable.extract_potential_gu
    ingredient_lbs = ingredient_extract / gravity_per_lb
    fermentable.lbs_in_recipe = ingredient_lbs

def get_total_required_gravity_units(final_gravity_gu, final_volume_g):
  """
  ex final_gravity_gu: 52 GUs
  """
  return final_gravity_gu * final_volume_g

def main():
  fermentables = [
    Fermentable("2 Row", 30, 0.8),
    Fermentable("DME", 20, 0.2, True)
  ]
  get_fermentables_amount(58, 5, fermentables, 0.7)

  print("Fermentables: ")
  for f in fermentables:
    print(" - {0}: {1} lbs".format(f.name, f.lbs_in_recipe))

main()
