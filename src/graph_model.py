import networkx as nx
from datetime import datetime
from enum import Enum

class NodeType(Enum):
    COMPONENT = "component"
    SPECIFICATION = "specification"
    SUPPLIER = "supplier"
    QUOTE = "quote"
    COST_ENTRY = "cost_entry"
    PROGRAM = "program"

class EdgeType(Enum):
    HAS_COMPONENT = "has_component"
    REQUIRES_SPEC = "requires_spec"
    QUOTED_BY = "quoted_by"
    SUBMITTED_BY = "submitted_by"
    HAS_COST = "has_cost"
    DEPENDS_ON = "depends_on"
    AFFECTS = "affects"

class NexusBOM:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.version_history = []
        self.current_tenure = "T1"

    def set_tenure(self, tenure):
        self.current_tenure = tenure

    def add_component(self, component_id, name, commodity, **attributes):
        self.graph.add_node(component_id, node_type=NodeType.COMPONENT.value, name=name, commodity=commodity, created_at=datetime.now().isoformat(), version=1, **attributes)
        self._log_change("ADD_COMPONENT", component_id, attributes)
        return component_id

    def add_specification(self, spec_id, name, requirement, category, **attributes):
        self.graph.add_node(spec_id, node_type=NodeType.SPECIFICATION.value, name=name, requirement=requirement, category=category, dell_requirement=requirement, supplier_feedback=None, dell_response=None, created_at=datetime.now().isoformat(), version=1, **attributes)
        self._log_change("ADD_SPEC", spec_id, {"requirement": requirement})
        return spec_id

    def add_supplier(self, supplier_id, name, **attributes):
        self.graph.add_node(supplier_id, node_type=NodeType.SUPPLIER.value, name=name, created_at=datetime.now().isoformat(), **attributes)
        return supplier_id

    def add_quote(self, quote_id, supplier_id, spec_id, response, unit_cost=None, meets_requirement=None, **attributes):
        self.graph.add_node(quote_id, node_type=NodeType.QUOTE.value, response=response, unit_cost=unit_cost, meets_requirement=meets_requirement, created_at=datetime.now().isoformat(), **attributes)
        self.graph.add_edge(spec_id, quote_id, edge_type=EdgeType.QUOTED_BY.value)
        self.graph.add_edge(quote_id, supplier_id, edge_type=EdgeType.SUBMITTED_BY.value)
        self._log_change("ADD_QUOTE", quote_id, {"supplier": supplier_id, "spec": spec_id, "meets_requirement": meets_requirement})
        return quote_id

    def add_cost_entry(self, cost_id, component_id, cost_type, amount, currency="USD", **attributes):
        self.graph.add_node(cost_id, node_type=NodeType.COST_ENTRY.value, cost_type=cost_type, amount=amount, currency=currency, created_at=datetime.now().isoformat(), **attributes)
        self.graph.add_edge(component_id, cost_id, edge_type=EdgeType.HAS_COST.value)
        return cost_id

    def link_component_to_spec(self, component_id, spec_id):
        self.graph.add_edge(component_id, spec_id, edge_type=EdgeType.REQUIRES_SPEC.value)

    def link_component_dependency(self, component_id, depends_on_id):
        self.graph.add_edge(component_id, depends_on_id, edge_type=EdgeType.DEPENDS_ON.value)

    def link_spec_affects_spec(self, spec_id, affected_spec_id):
        self.graph.add_edge(spec_id, affected_spec_id, edge_type=EdgeType.AFFECTS.value)

    def analyze_change_impact(self, node_id):
        impact = {"changed_node": node_id, "changed_node_data": dict(self.graph.nodes[node_id]), "affected_components": [], "affected_specs": [], "affected_quotes": [], "affected_costs": [], "affected_suppliers": [], "total_cost_impact": 0.0}
        visited = set()
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            node_data = self.graph.nodes[current]
            node_type = node_data.get("node_type")
            if current != node_id:
                if node_type == NodeType.COMPONENT.value:
                    impact["affected_components"].append({"id": current, **node_data})
                elif node_type == NodeType.SPECIFICATION.value:
                    impact["affected_specs"].append({"id": current, **node_data})
                elif node_type == NodeType.QUOTE.value:
                    impact["affected_quotes"].append({"id": current, **node_data})
                elif node_type == NodeType.COST_ENTRY.value:
                    impact["affected_costs"].append({"id": current, **node_data})
                    impact["total_cost_impact"] += node_data.get("amount", 0)
                elif node_type == NodeType.SUPPLIER.value:
                    impact["affected_suppliers"].append({"id": current, **node_data})
            queue.extend(self.graph.successors(current))
            queue.extend(self.graph.predecessors(current))
        return impact

    def calculate_total_bom_cost(self):
        total = 0.0
        breakdown_by_component = {}
        breakdown_by_type = {}
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == NodeType.COST_ENTRY.value:
                amount = data.get("amount", 0)
                cost_type = data.get("cost_type", "unknown")
                total += amount
                predecessors = list(self.graph.predecessors(node_id))
                for pred in predecessors:
                    pred_data = self.graph.nodes[pred]
                    if pred_data.get("node_type") == NodeType.COMPONENT.value:
                        comp_name = pred_data.get("name", pred)
                        breakdown_by_component.setdefault(comp_name, 0)
                        breakdown_by_component[comp_name] += amount
                breakdown_by_type.setdefault(cost_type, 0)
                breakdown_by_type[cost_type] += amount
        return {"total_bom_cost": round(total, 2), "by_component": breakdown_by_component, "by_cost_type": breakdown_by_type}

    def compare_suppliers_for_spec(self, spec_id):
        spec_data = self.graph.nodes[spec_id]
        dell_requirement = spec_data.get("dell_requirement", "")
        quotes = []
        for successor in self.graph.successors(spec_id):
            edge_data = self.graph.edges[spec_id, successor]
            if edge_data.get("edge_type") == EdgeType.QUOTED_BY.value:
                quote_data = dict(self.graph.nodes[successor])
                for quote_successor in self.graph.successors(successor):
                    sup_edge = self.graph.edges[successor, quote_successor]
                    if sup_edge.get("edge_type") == EdgeType.SUBMITTED_BY.value:
                        quote_data["supplier_name"] = self.graph.nodes[quote_successor].get("name")
                        quote_data["supplier_id"] = quote_successor
                quotes.append(quote_data)
        quotes.sort(key=lambda q: q.get("unit_cost") or float("inf"))
        compliant = [q for q in quotes if q.get("meets_requirement") is True]
        non_compliant = [q for q in quotes if q.get("meets_requirement") is False]
        lowest = min((q.get("unit_cost", float("inf")) for q in quotes if q.get("meets_requirement")), default=None)
        return {"spec_id": spec_id, "spec_name": spec_data.get("name"), "dell_requirement": dell_requirement, "supplier_quotes": quotes, "compliant_suppliers": compliant, "non_compliant_suppliers": non_compliant, "lowest_compliant_cost": lowest}

    def update_spec(self, spec_id, new_requirement, reason=""):
        node = self.graph.nodes[spec_id]
        old_requirement = node.get("requirement")
        old_version = node.get("version", 1)
        self.version_history.append({"node_id": spec_id, "tenure": self.current_tenure, "old_version": old_version, "new_version": old_version + 1, "old_value": old_requirement, "new_value": new_requirement, "reason": reason, "timestamp": datetime.now().isoformat()})
        node["requirement"] = new_requirement
        node["dell_requirement"] = new_requirement
        node["version"] = old_version + 1
        node["last_modified"] = datetime.now().isoformat()
        return {"change_record": self.version_history[-1], "impact": self.analyze_change_impact(spec_id)}

    def _log_change(self, action, node_id, details):
        self.version_history.append({"action": action, "node_id": node_id, "details": details, "tenure": self.current_tenure, "timestamp": datetime.now().isoformat()})