from ortools.sat.python import cp_model
import semantic_version


def compute_minimal_safe_version(current_version_str, available_versions_list, vulnerable_ranges):
    """
    Uses Google OR-Tools to find the minimal safe version upgrade.

    :param current_version_str: str (e.g., "1.2.0")
    :param available_versions_list: list of str (e.g., ["1.2.0", "1.2.1", "1.3.0", "2.0.0"])
    :param vulnerable_ranges: list of tuples (e.g., [("1.0.0", "1.2.5")]) representing >= introduced, < fixed
    :return: str representing the optimal safe version.
    """
    model = cp_model.CpModel()

    try:
        # Use .coerce() to handle non-strict semver strings like "1.3"
        current_version = semantic_version.Version.coerce(current_version_str)
        versions = [semantic_version.Version.coerce(v) for v in available_versions_list]
    except ValueError as e:
        print(f"Error parsing base versions: {e}")
        return "Invalid version format"

    # Define Boolean Variables (x_v)
    # version_vars[v] will be 1 if version v is selected, 0 otherwise.
    version_vars = {}
    for v in versions:
        version_vars[v] = model.NewBoolVar(f'version_{v}')

    # Constraint: Exactly one version must be selected
    model.AddExactlyOne(version_vars.values())

    # Constraint: Cannot downgrade (must be >= current_version)
    for v in versions:
        if v < current_version:
            model.Add(version_vars[v] == 0)

    # Constraint: The selected version MUST NOT fall into any vulnerable range
    for (introduced, fixed) in vulnerable_ranges:
        try:
            # Use .coerce() on OSV API ranges to handle incomplete strings
            intro_v = semantic_version.Version.coerce(introduced)
            fixed_v = semantic_version.Version.coerce(fixed)
        except ValueError as e:
            # Fail gracefully on completely mangled OSV strings without crashing Celery
            print(f"Skipping unparseable range {introduced} - {fixed}: {e}")
            continue

        for v in versions:
            if intro_v <= v < fixed_v:
                # If a version is within the vulnerable window, forbid it
                model.Add(version_vars[v] == 0)

    # Objective: Minimize the version jump (prefer closest safe version)
    # We assign a "cost" penalty. Major bumps cost more than minor, minor more than patch.
    objective_terms = []
    for v in versions:
        if v >= current_version:
            major_diff = v.major - current_version.major
            minor_diff = v.minor - current_version.minor
            patch_diff = v.patch - current_version.patch

            # Weighted cost formula
            cost = (major_diff * 10000) + (minor_diff * 100) + (patch_diff * 1)
            objective_terms.append(cost * version_vars[v])

    model.Minimize(sum(objective_terms))

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for v in versions:
            if solver.Value(version_vars[v]) == 1:
                return str(v)

    return "No safe upgrade path found"
