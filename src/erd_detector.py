import difflib

def compare_erd_dicts(old_data, new_data):
    changes = []
    all_keys = set(list(old_data.keys()) + list(new_data.keys()))
    for key in sorted(all_keys):
        old_val = old_data.get(key, "NOT PRESENT")
        new_val = new_data.get(key, "NOT PRESENT")
        if old_val != new_val:
            changes.append({"field": key, "old": str(old_val), "new": str(new_val), "type": "CHANGED"})
    return changes

def print_changes(changes):
    if not changes:
        print("No changes detected.")
        return
    print("Changes detected: " + str(len(changes)))
    for c in changes:
        print("  CHANGED: " + c["field"])
        print("    From: " + c["old"])
        print("    To:   " + c["new"])