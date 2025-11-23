def test_constraints_import():
    import pkgutil, importlib
    mods = []
    for _, name, _ in pkgutil.iter_modules(["context/constraints"]):
        m = importlib.import_module(f"context.constraints.{name}")
        assert hasattr(m, "add_constraints")
        mods.append(name)
    assert len(mods) >= 10
