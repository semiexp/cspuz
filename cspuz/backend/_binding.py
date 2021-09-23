def call_sugar_binding(binding_name: str, desc: str) -> str:
    if binding_name == 'pycsugar':
        import pycsugar
        return pycsugar.solver(desc)
    elif binding_name == 'enigma_csp':
        import enigma_csp
        return enigma_csp.solver(desc)
    else:
        raise ValueError(f'unknown binding: {binding_name}')
