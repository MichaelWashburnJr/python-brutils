DECIMAL_PLACES = 2

class Fermentable:
  def __init__(self, name, extract_potential_gu, percent_in_recipe, lovibond, is_extract = False):
    self.lovibond = lovibond
    self.name = name
    self.extract_potential_gu = extract_potential_gu
    self.percent_in_recipe = percent_in_recipe
    self.lbs_in_recipe = None
    self.is_extract = is_extract

def mcu_to_srm_estimate(mcu):
  """
  Morey equation
  """
  return 1.4922 * pow(mcu, 0.6859)

def get_fermentables_amount(final_gravity_gu, final_volume_g, fermentables, extract_efficiency_percent):
  total_gus = get_total_required_gravity_units(final_gravity_gu, final_volume_g)

  for fermentable in fermentables:
    ingredient_extract = fermentable.percent_in_recipe * total_gus
    gravity_per_lb = fermentable.extract_potential_gu
    if not fermentable.is_extract:
      gravity_per_lb *= extract_efficiency_percent

    ingredient_lbs = ingredient_extract / gravity_per_lb
    fermentable.lbs_in_recipe = round(ingredient_lbs, DECIMAL_PLACES)



def get_estimated_srm(final_volume_g, fermentables):
  total_mcu = 0
  for fermentable in fermentables:
    # malt color units
    mcu = fermentable.lovibond * fermentable.lbs_in_recipe / final_volume_g
    total_mcu += mcu
  return mcu_to_srm_estimate(total_mcu)

def get_total_required_gravity_units(final_gravity_gu, final_volume_g):
  """
  ex final_gravity_gu: 52 GUs
  """
  return final_gravity_gu * final_volume_g

def get_srm_descriptor(srm):
  if srm < 3:
    return "Very pale"
  elif srm < 4:
    return "Pale"
  elif srm < 6:
    return "Gold"
  elif srm < 9:
    return "Amber"
  elif srm < 14:
    return "Deep amber/light copper"
  elif srm < 17:
    return "Copper"
  elif srm < 18:
    return "Deep copper/light brown"
  elif srm < 22:
    return "Brown"
  elif srm < 30:
    return "Dark brown"
  elif srm < 35:
    return "Very dark brown"
  elif srm < 40:
    return "Black"
  else:
    return "Black, opaque"

def hot_to_cold_water_volume(hot_water_volume_g):
  return hot_water_volume_g * 0.96

def cold_to_hot_water_volume(cold_water_volume_g):
  return cold_water_volume_g / 0.96

def calc_mash_and_sparge_water(fermentables, batch_size_g, mash_ratio_quarts_per_lb, trub_loss_g, mash_tun_false_bottom_volume_g, sparge_water_false_bottom_volume_g, equipment_loss_g, evap_rate_gal_per_hour, boil_length_min):
  total_grain_weight_lbs = 0
  for fermentable in fermentables:
    if not fermentable.is_extract:
      total_grain_weight_lbs += fermentable.lbs_in_recipe

  data = {}

  total_water_g = batch_size_g
  data['starting_water'] = total_water_g

  total_water_g += trub_loss_g
  data['final_boil_volume'] = total_water_g


  evap_rate_gal_per_min = evap_rate_gal_per_hour/60
  evap_loss_g = evap_rate_gal_per_min*boil_length_min
  total_water_g += evap_loss_g
  data['after_evaporation'] = total_water_g

  total_water_g += equipment_loss_g
  data['after_equipment_loss'] = total_water_g


  grain_water_loss_g = total_grain_weight_lbs * 0.2
  total_water_g += grain_water_loss_g
  data['after_grain_loss'] = total_water_g

  # account for shrinkage
  total_water_g = cold_to_hot_water_volume(total_water_g)
  data['with_shrinkage'] = total_water_g

  mash_water_cold_gal = hot_to_cold_water_volume(mash_tun_false_bottom_volume_g) + hot_to_cold_water_volume(total_grain_weight_lbs * mash_ratio_quarts_per_lb)/4
  sparge_water_g = sparge_water_false_bottom_volume_g + total_water_g - mash_water_cold_gal

  data['mash'] = mash_water_cold_gal
  data['sparge'] = sparge_water_g
  data['total'] = total_water_g
  return data


def main():
  # fermentables = [
  #   Fermentable("Wheat", 38, 0.2, 8),
  #   Fermentable("Honey", 33, 0.2, 0, True),
  #   Fermentable("Two-row", 36, 0.6, 2)
  # ]
  fermentables = [
    Fermentable("Wheat", 38, 1, 8),
  ]
  get_fermentables_amount(39.95, 5.5, fermentables, 0.68)

  print("Fermentables: ")
  for f in fermentables:
    print(" - {0}: {1} lbs".format(f.name, f.lbs_in_recipe))
  srm = get_estimated_srm(5.5, fermentables)
  print("Estimated SRM: {0} ({1})".format(srm, get_srm_descriptor(srm)))

  water_details = calc_mash_and_sparge_water(fermentables, 5, 1.33, 0.5, 0, 0, 1, 0.275, 90)
  print('Mash Water: {0} gallons'.format(water_details['mash']))
  print('Sparge Water: {0} gallons'.format(water_details['sparge']))
  # print('Total water lost: {0} gallons'.format(water_details['lost']))
  print('Total water: {0} gallons'.format(water_details['total']))

main()
