from src.graph_model import NexusBOM


def main():
    bom = NexusBOM()
    bom.set_tenure("T1")

    print("=" * 60)
    print("STEP 1: Building BOM Structure")
    print("=" * 60)

    bom.add_component("COMP-PANEL", "LCD Panel",
                       commodity="Display", owner_gcm="Alice")
    bom.add_component("COMP-BEZEL", "Front Bezel",
                       commodity="Plastics", owner_gcm="Bob")
    bom.add_component("COMP-CHASSIS", "Metal Chassis",
                       commodity="Metals", owner_gcm="Carol")
    bom.add_component("COMP-PCBA", "Main PCBA",
                       commodity="Electronics", owner_gcm="Dave")
    bom.add_component("COMP-STAND", "Monitor Stand",
                       commodity="Metals", owner_gcm="Carol")

    bom.link_component_dependency("COMP-BEZEL", "COMP-PANEL")
    bom.link_component_dependency("COMP-CHASSIS", "COMP-PANEL")

    print("  Added 5 components")

    print("\nSTEP 2: Adding ERD Specifications")

    bom.add_specification("SPEC-HDR", "HDR Support",
                          requirement="HDR 600, peak 600 nits",
                          category="Panel Performance")
    bom.add_specification("SPEC-USB", "USB-C Connectivity",
                          requirement="USB-C 90W PD, DP Alt Mode",
                          category="Connectivity")
    bom.add_specification("SPEC-COLOR", "Color Calibration",
                          requirement="Delta E < 2, sRGB 99%",
                          category="Color Performance")

    bom.link_component_to_spec("COMP-PANEL", "SPEC-HDR")
    bom.link_component_to_spec("COMP-PANEL", "SPEC-COLOR")
    bom.link_component_to_spec("COMP-PCBA", "SPEC-USB")
    bom.link_spec_affects_spec("SPEC-HDR", "SPEC-COLOR")

    print("  Added 3 specs")

    print("\nSTEP 3: Adding Costs")

    bom.add_cost_entry("COST-PANEL-MAT", "COMP-PANEL",
                       "material", 125.00)
    bom.add_cost_entry("COST-PANEL-TOOL", "COMP-PANEL",
                       "tooling", 8.50)
    bom.add_cost_entry("COST-BEZEL-MAT", "COMP-BEZEL",
                       "material", 3.20)
    bom.add_cost_entry("COST-BEZEL-CMF", "COMP-BEZEL",
                       "CMF", 1.15)
    bom.add_cost_entry("COST-BEZEL-TOOL", "COMP-BEZEL",
                       "tooling", 0.85)
    bom.add_cost_entry("COST-CHASSIS-MAT", "COMP-CHASSIS",
                       "material", 7.80)
    bom.add_cost_entry("COST-PCBA-MAT", "COMP-PCBA",
                       "material", 22.00)
    bom.add_cost_entry("COST-PCBA-ASSY", "COMP-PCBA",
                       "assembly", 4.50)
    bom.add_cost_entry("COST-STAND-MAT", "COMP-STAND",
                       "material", 6.40)

    print("  Added 9 cost entries")

    print("\nSTEP 4: Adding Suppliers")

    bom.add_supplier("SUP-LGD", "LG Display")
    bom.add_supplier("SUP-AUO", "AU Optronics")
    bom.add_supplier("SUP-BOE", "BOE Technology")
    bom.add_supplier("SUP-INX", "Innolux")

    bom.add_quote("QUO-LGD-HDR", "SUP-LGD", "SPEC-HDR",
                  response="HDR600 supported, peak 610 nits",
                  unit_cost=125.00, meets_requirement=True)
    bom.add_quote("QUO-AUO-HDR", "SUP-AUO", "SPEC-HDR",
                  response="HDR400 max, peak 420 nits",
                  unit_cost=98.00, meets_requirement=False)
    bom.add_quote("QUO-BOE-HDR", "SUP-BOE", "SPEC-HDR",
                  response="HDR600 supported, peak 595 nits",
                  unit_cost=110.00, meets_requirement=True)
    bom.add_quote("QUO-INX-HDR", "SUP-INX", "SPEC-HDR",
                  response="HDR600 supported, peak 601 nits",
                  unit_cost=118.00, meets_requirement=True)

    print("  Added 4 suppliers")

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    cost_report = bom.calculate_total_bom_cost()
    print(f"\nTotal BOM Cost: ${cost_report['total_bom_cost']}")
    print("\n  By Component:")
    for comp, cost in cost_report["by_component"].items():
        print(f"    {comp}: ${cost:.2f}")
    print("\n  By Cost Type:")
    for ctype, cost in cost_report["by_cost_type"].items():
        print(f"    {ctype}: ${cost:.2f}")

    print(f"\n--- Supplier Comparison for HDR ---")
    comparison = bom.compare_suppliers_for_spec("SPEC-HDR")
    print(f"  Dell Requirement: {comparison['dell_requirement']}")
    print(f"  Lowest Compliant: ${comparison['lowest_compliant_cost']}")
    for q in comparison["supplier_quotes"]:
        status = "PASS" if q.get("meets_requirement") else "FAIL"
        print(f"    [{status}] {q.get('supplier_name')}: "
              f"${q.get('unit_cost')} - {q.get('response')}")

    print(f"\n" + "=" * 60)
    print("SIMULATING DESIGN CHANGE")
    print("=" * 60)

    change_result = bom.update_spec(
        "SPEC-HDR",
        new_requirement="HDR 1000, peak 1000 nits",
        reason="Customer upgrade"
    )

    cr = change_result["change_record"]
    impact = change_result["impact"]

    print(f"\n  From: {cr['old_value']}")
    print(f"  To:   {cr['new_value']}")
    print(f"  Version: v{cr['old_version']} -> v{cr['new_version']}")

    print(f"\n  IMPACT:")
    print(f"  Components affected: {len(impact['affected_components'])}")
    for c in impact["affected_components"]:
        print(f"    - {c['name']} (notify {c.get('owner_gcm', '?')})")
    print(f"
