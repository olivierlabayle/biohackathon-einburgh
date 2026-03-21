import cobra
from cobra.io import read_sbml_model, write_sbml_model

MODEL_PATH = "salmonella"
OBJECTIVE = "BIOMASS_iRR1083_1"
DIRECTION = "max"


def optimize_model(model: cobra.Model, objective: str, direction: str = "max"):
    """
    Optimize a COBRA model on a given objective.
    
    Args:
        model (cobra.Model): The model to optimize.
        objective (str): The objective to optimize.
        
    Returns:
        cobra.Model: The optimized model.
    """
    model.objective = objective
    model.objective_direction = direction
    solution = model.optimize()
    max_growth = solution.objective_value

    return model, max_growth

def compute_try(model: cobra.Model):
    """
    Compute TRY

    From Oliver Konzock, Jens Nielsen, TRYing to evaluate production costs in microbial biotechnology, Trends in Biotechnology, Volume 42, Issue 11, 2024, Pages 1339-1347, ISSN 0167-7799, https://doi.org/10.1016/j.tibtech.2024.04.007. (https://www.sciencedirect.com/science/article/pii/S0167779924001197):
    - Titer (product amount per volume, cP) represents the final concentration of the product in the fermentation process.
    - Rate represents the productivity of the cell factory.
    - Yield (product produced per substrate consumed, YSP) represents the amount of product produced per amount of substrate used.
    """
    pass 

def main():
    model = read_sbml_model(MODEL_PATH)

    model_optimized, max_value = optimize_model(model, OBJECTIVE, DIRECTION)
    print(max_value)

    compute_try(model_optimized)

    write_sbml_model(model_optimized, MODEL_PATH.replace(".xml", "_optimized.xml"))

if __name__ == "__main__":
    main()
