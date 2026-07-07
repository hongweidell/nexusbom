import pandas as pd
from src.graph_model import NexusBOM


def load_erd_from_excel(bom, filepath, sheet_name="ERD"):
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    for index, row in df.iterrows():
        spec_id = str(row.get("Spec ID", f"SPEC-{index}"))
        bom.add_specification(
            spec_id=spec_id,
            name=str(row.get("Requirement", "")),
            requirement=str(row.get("Dell Requirement", "")),
            category=str(row.get("Category", "General"))
        )

    print(f"Loaded {len(df)} specifications from {filepath}")
    return bom


def load_bom_costs_from_excel(bom, filepath, sheet_name="BOM"):
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    for index, row in df.iterrows():
        comp_id = str(row.get("Component ID", f"COMP-{index}"))

        bom.add_component(
            component_id=comp_id,
            name=str(row.get("Component Name", "")),
            commodity=str(row.get("Commodity", ""))
        )

        for cost_type in ["Material Cost", "Tooling Cost",
                          "Assembly Cost", "CMF Cost"]:
            amount = row.get(cost_type, 0)
            if pd.notna(amount) and amount > 0:
                cost_id = (f"COST-{comp_id}-"
                           f"{cost_type.split()[0].lower()}")
                bom.add_cost_entry(
                    cost_id=cost_id,
                    component_id=comp_id,
                    cost_type=cost_type.split()[0].lower(),
                    amount=float(amount)
                )

    print(f"Loaded {len(df)} components from {filepath}")
    return bom
