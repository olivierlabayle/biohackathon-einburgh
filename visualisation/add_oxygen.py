import cobra
from cobra import Reaction, Metabolite


def add_oxygen_to_model(model):
    """
    Add oxygen exchange reaction to the model if it doesn't exist.
    
    Args:
        model (cobra.Model): The COBRA model to modify.
    """
    if not model.reactions.has_id("EX_o2_e"):
        new_met = Metabolite(
            "o2_e", 
            formula="O2", 
            name="Oxygen", 
            compartment="e"
        )
        model.add_metabolites([new_met])

        o2_exchange = Reaction("EX_o2_e")
        o2_exchange.name = "Oxygen Exchange"
        o2_exchange.lower_bound = -1000.0  # Allow unlimited uptake (Submerged)
        o2_exchange.upper_bound = 1000.0   # Allow secretion (though rare)

        o2_exchange.add_metabolites({model.metabolites.get_by_id("o2_e"): -1})

        model.add_reactions([o2_exchange])