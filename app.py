import streamlit as st
from src.graph_model import NexusBOM
from src.erd_detector import compare_erd_dicts

PRODUCT = "AW2726DM"

def make_id(assembly, component, tenure="T1"):
    return PRODUCT + "-" + assembly + "-" + component + "-" + tenure

def build_sample_bom():
    bom = NexusBOM()
    bom.set_tenure("T1")
    panel_id = make_id("PANEL", "MODULE")
    bezel_id = make_id("FTA", "FBEZEL")
    chassis_id = make_id("MCA", "MAINCHASSIS")
    pcba_id = make_id("PCBA", "MAINBOARD")
    stand_id = make_id("STA", "STAND")
    bom.add_component(panel_id, "LCD Panel", commodity="Display", owner_gcm="Alice")
    bom.add_component(bezel_id, "Front Bezel", commodity="Plastics", owner_gcm="Bob")
    bom.add_component(chassis_id, "Metal Chassis", commodity="Metals", owner_gcm="Carol")
    bom.add_component(pcba_id, "Main PCBA", commodity="Electronics", owner_gcm="Dave")
    bom.add_component(stand_id, "Monitor Stand", commodity="Metals", owner_gcm="Carol")
    bom.link_component_dependency(bezel_id, panel_id)
    bom.link_component_dependency(chassis_id, panel_id)
    hdr_id = make_id("SPEC", "HDR")
    usb_id = make_id("SPEC", "USBC")
    color_id = make_id("SPEC", "COLOR")
    bom.add_specification(hdr_id, "HDR Support", requirement="HDR 600 nits", category="Panel Performance")
    bom.add_specification(usb_id, "USB-C", requirement="USB-C 90W PD", category="Connectivity")
    bom.add_specification(color_id, "Color", requirement="sRGB 99 percent", category="Color")
    bom.link_component_to_spec(panel_id, hdr_id)
    bom.link_component_to_spec(panel_id, color_id)
    bom.link_component_to_spec(pcba_id, usb_id)
    bom.link_spec_affects_spec(hdr_id, color_id)
    bom.add_cost_entry(make_id("COST", "PANEL-MAT"), panel_id, "material", 125.00)
    bom.add_cost_entry(make_id("COST", "PANEL-TOOL"), panel_id, "tooling", 8.50)
    bom.add_cost_entry(make_id("COST", "BEZEL-MAT"), bezel_id, "material", 3.20)
    bom.add_cost_entry(make_id("COST", "BEZEL-CMF"), bezel_id, "CMF", 1.15)
    bom.add_cost_entry(make_id("COST", "BEZEL-TOOL"), bezel_id, "tooling", 0.85)
    bom.add_cost_entry(make_id("COST", "CHASSIS-MAT"), chassis_id, "material", 7.80)
    bom.add_cost_entry(make_id("COST", "PCBA-MAT"), pcba_id, "material", 22.00)
    bom.add_cost_entry(make_id("COST", "PCBA-ASSY"), pcba_id, "assembly", 4.50)
    bom.add_cost_entry(make_id("COST", "STAND-MAT"), stand_id, "material", 6.40)
    lgd_id = make_id("PANEL", "LGD")
    auo_id = make_id("PANEL", "AUO")
    boe_id = make_id("PANEL", "BOE")
    inx_id = make_id("PANEL", "INX")
    bom.add_supplier(lgd_id, "LG Display")
    bom.add_supplier(auo_id, "AU Optronics")
    bom.add_supplier(boe_id, "BOE Technology")
    bom.add_supplier(inx_id, "Innolux")
    bom.add_quote(make_id("QUO", "LGD-HDR"), lgd_id, hdr_id, response="peak 610 nits", unit_cost=125.00, meets_requirement=True)
    bom.add_quote(make_id("QUO", "AUO-HDR"), auo_id, hdr_id, response="peak 420 nits", unit_cost=98.00, meets_requirement=False)
    bom.add_quote(make_id("QUO", "BOE-HDR"), boe_id, hdr_id, response="peak 595 nits", unit_cost=110.00, meets_requirement=True)
    bom.add_quote(make_id("QUO", "INX-HDR"), inx_id, hdr_id, response="peak 601 nits", unit_cost=118.00, meets_requirement=True)
    return bom, hdr_id

st.set_page_config(page_title="NexusBOM", page_icon="🔗", layout="wide")
st.title("NexusBOM")
st.caption("Graph-Powered RFI/RFQ Intelligence for Dell OLP")

bom, hdr_id = build_sample_bom()

tab1, tab2, tab3 = st.tabs(["BOM Cost", "Supplier Comparison", "ERD Change Detector"])

with tab1:
    st.header("BOM Cost Breakdown")
    cost_report = bom.calculate_total_bom_cost()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total BOM Cost", "$" + str(cost_report["total_bom_cost"]))
    col2.metric("Components", str(len(cost_report["by_component"])))
    col3.metric("Cost Types", str(len(cost_report["by_cost_type"])))
    st.subheader("By Component")
    for comp, cost in cost_report["by_component"].items():
        st.write(comp + ":  $" + str(round(cost, 2)))
    st.subheader("By Cost Type")
    for ctype, cost in cost_report["by_cost_type"].items():
        st.write(ctype + ":  $" + str(round(cost, 2)))

with tab2:
    st.header("Supplier Comparison")
    comparison = bom.compare_suppliers_for_spec(hdr_id)
    st.write("Dell Requirement: " + comparison["dell_requirement"])
    st.write("Lowest Compliant Price: $" + str(comparison["lowest_compliant_cost"]))
    st.subheader("All Suppliers")
    for q in comparison["supplier_quotes"]:
        if q.get("meets_requirement"):
            st.success("[PASS] " + str(q.get("supplier_name")) + " — $" + str(q.get("unit_cost")) + " — " + str(q.get("response")))
        else:
            st.error("[FAIL] " + str(q.get("supplier_name")) + " — $" + str(q.get("unit_cost")) + " — " + str(q.get("response")))
    st.subheader("Simulate Design Change")
    new_req = st.text_input("Enter new HDR requirement", value="HDR 1000 nits")
    reason = st.text_input("Reason for change", value="Customer upgrade")
    if st.button("Run Impact Analysis"):
        change_result = bom.update_spec(hdr_id, new_req, reason=reason)
        cr = change_result["change_record"]
        impact = change_result["impact"]
        st.write("From: " + str(cr["old_value"]))
        st.write("To: " + str(cr["new_value"]))
        st.write("Version: v" + str(cr["old_version"]) + " to v" + str(cr["new_version"]))
        st.subheader("Impact")
        for c in impact["affected_components"]:
            st.warning(c["name"] + " — notify: " + str(c.get("owner_gcm", "?")))
        for s in impact["affected_suppliers"]:
            st.info(s["name"])
        st.write("Cost exposure: $" + str(round(impact["total_cost_impact"], 2)))

with tab3:
    st.header("ERD Change Detector")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ERD Version 1 (Old)")
        v1_brightness = st.text_input("Panel Brightness v1", value="400 nits")
        v1_usb = st.text_input("USB Connectivity v1", value="USB-A 3.0 only")
        v1_color = st.text_input("Color Coverage v1", value="sRGB 95 percent")
        v1_hdr = st.text_input("HDR Support v1", value="HDR 400")
        v1_response = st.text_input("Response Time v1", value="5ms")
    with col2:
        st.subheader("ERD Version 2 (New)")
        v2_brightness = st.text_input("Panel Brightness v2", value="600 nits")
        v2_usb = st.text_input("USB Connectivity v2", value="USB-C 90W PD")
        v2_color = st.text_input("Color Coverage v2", value="sRGB 99 percent")
        v2_hdr = st.text_input("HDR Support v2", value="HDR 600")
        v2_response = st.text_input("Response Time v2", value="1ms")
    if st.button("Detect Changes"):
        erd_v1 = {"Panel Brightness": v1_brightness, "USB Connectivity": v1_usb, "Color Coverage": v1_color, "HDR Support": v1_hdr, "Response Time": v1_response}
        erd_v2 = {"Panel Brightness": v2_brightness, "USB Connectivity": v2_usb, "Color Coverage": v2_color, "HDR Support": v2_hdr, "Response Time": v2_response}
        changes = compare_erd_dicts(erd_v1, erd_v2)
        if not changes:
            st.success("No changes detected")
        else:
            st.warning(str(len(changes)) + " changes detected")
            for c in changes:
                st.write("CHANGED: " + c["field"])
                st.write("From: " + c["old"])
                st.write("To: " + c["new"])
                if "Brightness" in c["field"] or "HDR" in c["field"]:
                    st.error("Notify: Alice (Panel GCM), LG, BOE, AUO, INX")
                elif "USB" in c["field"]:
                    st.error("Notify: Dave (PCBA GCM)")
                elif "Color" in c["field"] or "Response" in c["field"]:
                    st.error("Notify: Alice (Panel GCM)")
                st.divider()