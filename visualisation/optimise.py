"""
use run_optimization() to optimize a COBRA model on a given objective.

Input:
    model_path (str): Path to the SBML model file.
    objective (str): The objective to optimize.
    direction (str): The direction of optimization (max or min).

Output:
    Optimized model in .xml format at {model_path}_optimized.xml
"""

import cobra
from cobra.io import read_sbml_model, write_sbml_model
from media import MEDIA

def optimize_model(model: cobra.Model, objective: str, direction: str = "max"):
    """
    Optimize a COBRA model on a given objective.
    
    Args:
        model (cobra.Model): The model to optimize.
        objective (str): The reaction id to optimize.
        direction (str): The direction of optimization (max or min).
    Returns:
        cobra.Model: The optimized model.
    """
    model.objective = objective
    model.objective_direction = direction
    solution = model.optimize()
    max_growth = solution.objective_value

    return model, max_growth

def compute_try(model: cobra.Model, product_id: str, substrates: str, biomass_concentration: float):
    """
    Compute TRY

    From Oliver Konzock, Jens Nielsen, TRYing to evaluate production costs in microbial biotechnology, Trends in Biotechnology, Volume 42, Issue 11, 2024, Pages 1339-1347, ISSN 0167-7799, https://doi.org/10.1016/j.tibtech.2024.04.007. (https://www.sciencedirect.com/science/article/pii/S0167779924001197):
    - Yield (product produced per substrate consumed, YSP) represents the amount of product produced per amount of substrate used.
    - Rate represents the productivity of the cell factory.
    - Titer (product amount per volume, cP) represents the final concentration of the product in the fermentation process.
    """

    print(f"Computing TRY for product: {product_id}, substrate: {substrates}, biomass concentration: {biomass_concentration}")

    # 1. Yield (Y_SP)
    # Yield = Flux of Product / |Flux of Substrate|
    product_flux = model.reactions.get_by_id(product_id).flux
    total_substrate_flux = sum(abs(model.reactions.get_by_id(s).flux) for s in substrates)
    yield_val = product_flux / total_substrate_flux if total_substrate_flux != 0 else 0

    # 2. Rate (Productivity)
    # In COBRApy, the flux value is the biomass-specific rate (mmol / gDW / h)
    rate = product_flux

    # Estimated Titer (mmol/L) = Rate * Biomass
    titer = rate * biomass_concentration

    print(f"Yield: {yield_val:.4f} mol/mol")
    print(f"Rate: {rate:.4f} mmol/gDW/h")
    print(f"Titer (after 1h): {titer:.4f} mmol/L")

    return yield_val, rate, titer

def run_optimization(model_path: str, substrates: list[str], biomass_concentration: float, objective: str, direction: str = "max"):
    """
    Run the optimization workflow.
    
    Args:
        model_path (str): Path to the SBML model file.
        objective (str): The reaction id to optimize.
        direction (str): The direction of optimization (max or min).
    """

    if not model_path.endswith(".xml"):
        model = cobra.io.load_model(model_path)
    else:
        model = read_sbml_model(model_path)

    model_optimized, max_value = optimize_model(model, objective, direction)
    print(max_value)

    compute_try(model_optimized, objective, substrates, biomass_concentration)

    write_sbml_model(model_optimized, model_path.replace(".xml", "_optimized.xml"))

if __name__ == "__main__":

    MODEL_PATH = "salmonella"
    substrates = ["EX_glc__D_e"]
    BIOMASS_CONCENTRATION = 0.5
    OBJECTIVE = "BIOMASS_iRR1083_1"
    DIRECTION = "max"

    run_optimization(MODEL_PATH, substrates, BIOMASS_CONCENTRATION, OBJECTIVE, DIRECTION)
