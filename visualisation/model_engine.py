import cobra
import pandas as pd
from cobra.io import load_model

def load_fungal_model(strain_name):
    """
    In a real app, this would trigger a reconstruction pipeline.
    For the MVP, we load a high-quality template model (e.g., iML1515 or a fungal core).
    """
    # Loading a demo model included with COBRApy for functional testing
    model = load_model("textbook")
    model.name = strain_name
    return model

def run_fba_simulation(model, diet_updates):
    """
    Updates the model with user-defined media and runs Flux Balance Analysis.
    diet_updates: dictionary like {'EX_glc__D_e': -10.0}
    """
    with model:
        # Update exchange reactions (media)
        for rxn_id, flux in diet_updates.items():
            if model.reactions.has_id(rxn_id):
                model.reactions.get_by_id(rxn_id).lower_bound = flux

        solution = model.optimize()
        return solution

def get_sensitivity_data(model, nutrient_id, max_flux=20, step=2):
    """Calculates how growth changes as a specific nutrient varies."""
    if step <= 0:
        raise ValueError("step must be greater than 0")
    if max_flux < 0:
        raise ValueError("max_flux must be non-negative")
    if not model.reactions.has_id(nutrient_id):
        raise ValueError(f"Nutrient reaction not found: {nutrient_id}")

    growth_rates = []
    flux_range = [i for i in range(0, int(max_flux) + 1, step)]

    for val in flux_range:
        with model:
            model.reactions.get_by_id(nutrient_id).lower_bound = -val
            sol = model.optimize()
            growth_rates.append(sol.objective_value if sol.status == 'optimal' else 0)

    return pd.DataFrame({"Flux": flux_range, "Growth Rate": growth_rates})