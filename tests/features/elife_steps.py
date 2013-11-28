from lettuce import *
import provider.elife as elifelib

@step('I create an elife provider')
def i_create_an_elife_provider(step):
  try:
    world.settings = world.settings
  except AttributeError:
    world.settings = None

  world.elife = elifelib.elife(world.settings)
  assert world.elife is not None, \
    "Got elife %s" % world.elife

@step('I get a value from the elife provider for the attribute (\S+)')
def i_get_a_value_from_the_elife_provider_for_the_attribute(step, attribute):
  attr = eval("world.elife." + attribute)
  world.value = attr
  assert world.value is not None, \
    "Got value %s" % world.value
    
@step('I have the value (\S+)')
def i_have_the_value(step, value):
  assert world.value == value, \
    "Got value %s" % world.value