"""
@author: Jack Charles   http://jackcharlesconsulting.com/
Introduction for creating a worksheet in Python and NiceGUI
"""

#required imports
import math
from nicegui import app, ui

#generic error handling for all functions
def err_handle(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ZeroDivisionError as e:
            print(f"Error calling {func.__name__}: {e}. Returning NaN.")
            return float('nan') # Example of returning a safe value
        except ValueError as e:
            print(f"Error calling {func.__name__}: {e}. Returning NaN.")
            return float('nan') # Example of returning a safe value
        except TypeError as e:
            print(f"Error calling {func.__name__}: {e}. Check input types.")
            raise # Re-raise the exception for further handling
        except OverflowError as e:
            print(f"Error calling {func.__name__}: {e}. Value too large.")
            return float('inf') if args[0] > 0 else float('-inf') # Example of handling overflow
        except Exception as e:
            print(f"An unexpected error occurred calling {func.__name__}: {e}")
            raise
    return wrapper

#basic equations
@err_handle
def calc_fluid_velocity(fluid_rate, diameter, inner_diameter=0):
    #flow_rate:bbl/min   diameter, inner_diameter:in   output:ft/s
    #this def only needs one diameter input, other can be 0. No preference on order
    _CONST = 13.475
    if (diameter ** 2 - inner_diameter ** 2) == 0: 
        fluid_velocity = 0
    else: 
        fluid_velocity = _CONST * 4 * fluid_rate / math.pi / (diameter ** 2 - inner_diameter ** 2)
    return fluid_velocity

@err_handle
def calc_NRe_newton(fluid_velocity, hydraulic_diameter, fluid_density, fluid_viscosity):
    #fluid_velocity:ft/s  hydraulic_diameter:in     fluid_density:ppg     fluid_viscosity:cP
    _CONST = 927.6866
    NRe_newton = _CONST * fluid_velocity * hydraulic_diameter * fluid_density / fluid_viscosity
    return NRe_newton

@err_handle
def calc_friction_colebrook(hydraulic_diameter, NRe, roughness):    
    #hydraulic_diameter, roughness:in
    #Fanning friction factor, Colebrook-White implicit solution. Note Darcy = 4x Fanning friction
    #ff = 1 / (f ** 0.5) + 4 * math.log10(e / 3.7065 + 1.2613 / (NRe * (f ** 0.5)))
    if NRe < 2100:
        friction_colebrook = 16 / NRe
    else:
        _e = roughness / hydraulic_diameter
        #Newton-Raphson solution
        f1 = 0.00001
        f01 = 1
        dF = 0.000005
        while f01 > 0.000000001:
            f0 = f1
            #ff1 = 1 / (f0 ** 0.5) + 2 * log10(_e / 3.7065 + 2.51 / (NRe * (f0 ** 0.5)))                    #Darcy friction factor
            #ff2 = 1 / ((f0 + dF) ** 0.5) + 2 * log10(_e / 3.7065 + 2.51 / (NRe * ((f0 + dF) ** 0.5)))
            ff1 = 1 / (f0 ** 0.5) + 4 * math.log10(_e / 3.7065 + 1.2613 / (NRe * (f0 ** 0.5)))              #Fanning friction factor
            ff2 = 1 / ((f0 + dF) ** 0.5) + 4 * math.log10(_e / 3.7065 + 1.2613 / (NRe * ((f0 + dF) ** 0.5)))
            f1 = f0 - ff1 / ((ff2 - ff1) / dF)
            f01 = abs(f1 - f0)
        friction_colebrook = f1
    return friction_colebrook

#Server Main Page
@ui.page('/')
def front_page():
    ui.label("Welcome to the NiceGUI server")
    ui.link('Link to Friction Calculator', '/friction')
    ui.button('Shutdown Server Safely', on_click=app.shutdown)

#Solve Friction Factor Page
@ui.page('/friction')
def solve_friction():

#Create layout of program
    ui.label("Fluid Friction Calculation")
    ui.link('Back to Main', '/')

    with ui.row():
        velocity_card = ui.card()
        with velocity_card:
            ui.label("Fluid Velocity")
            fluid_rate = ui.number(label="Flow Rate", value=3, min=0, format='%.1f', step=0.1, suffix="bpm")
            diameter = ui.number(label="Diameter", value=3, min=0, format='%.3f', step=0.1, suffix="in")
            inner_diameter = ui.number(label="Concentric Diameter", value=0.000, min=0, format='%.1f', step=0.1, suffix="in")
            velocity_result = ui.label(f"Fluid Velocity {app.storage.general['Units']['Velocity']}")
            velocity_solve = ui.button("Solve Velocity", on_click=lambda: solve_fluid_velocity())

        with ui.card():
            ui.label("Reynold's Number")   
            fluid_density = ui.number(label="Fluid Density", value=9.6, min=0, format='%.1f', step=0.1, suffix='ppg')
            fluid_viscosity = ui.number(label="Fluid Viscosity", value=2.1, min=0, format='%.1f', step=0.1, suffix='cP')
            NRe_result = ui.label(f"Reynold's Number ")
            NRe_result_regime = ui.label()
            NRe_result_regime.visible = False
            ui.button("Solve Reynold's Number", on_click=lambda: (
                solve_NRe_newton(fluid_velocity, (diameter.value - inner_diameter.value), fluid_density.value, fluid_viscosity.value)))

            NRe_result_toggle = ui.label("1")
            NRe_result_toggle.visible = False
          
        with ui.card():
            ui.label("Friction Factor")   
            roughness = ui.number(label="Roughness", value=0.005, min=0, format='%.3f', step=0.001,suffix='in')
            friction_factor_value = ui.label(f"Friction Factor ") 
            ui.button("Solve Friction Factor", on_click=lambda: solve_friction_colebrook())
    
    #Define the functions to be used when clicking on buttons    
    #Example of assign result to a global variable
    def solve_fluid_velocity():
        global fluid_velocity
        fluid_velocity = calc_fluid_velocity(fluid_rate.value, diameter.value, inner_diameter.value)                        
        velocity_result.text = f"Fluid Velocity {fluid_velocity:.2f} ft/s"
         
    #Example of assign result to hidden label, which will be used in subsequent function
    def solve_NRe_newton(fluid_velocity, hydraulic_diameter, fluid_density, fluid_viscosity):
        NRe_newton = calc_NRe_newton(fluid_velocity, hydraulic_diameter, fluid_density, fluid_viscosity)
        if NRe_newton < 2100:
            flow_regime = "Laminar"
        else:
            flow_regime = "Turbulent"
        NRe_result.text = f"Reynold's Number {NRe_newton:.0f}."
        NRe_result_regime.text = f"Flow is {flow_regime}."
        NRe_result_regime.visible = True
    #assign result to hidden label
        NRe_result_toggle.text = NRe_newton
        NRe_result_toggle.visible = True   

    #Examle of reading from a text label, and using app.storage.client for storage
    def solve_friction_colebrook():
        hydraulic_diameter = diameter.value - inner_diameter.value
        friction_factor = calc_friction_colebrook(hydraulic_diameter, float(NRe_result_toggle.text), roughness.value)
        app.storage.client['Friction Calculator'] = {}
        app.storage.client['Friction Calculator']['ff'] = friction_factor
        friction_factor_value.bind_text_from(app.storage.client['Friction Calculator'],'ff',backward=lambda x: f"FF {x:.5f}")
         
ui.run()