"""Display finishes shared by the models: one palette, assigned per part.

These are visual finishes for the viewer's Render display and for GLB export (base colour, roughness,
metalness). Metalness is kept moderate: near 1 the default Render lighting turns large surfaces almost
black. They are not physical material assignments: no alloy, density or mass is implied
(docs/model-specs.md). Colours are kept mid to light so shape stays readable with plain shading too.
"""

FINISHES = {
    "machined_steel": {"name": "Machined steel", "baseColor": "#C3C7CC", "roughness": 0.38, "metalness": 0.55},
    "cast_alloy": {"name": "Cast alloy", "baseColor": "#CACDD1", "roughness": 0.60, "metalness": 0.35},
    "dark_steel": {"name": "Dark oxide steel", "baseColor": "#5C6068", "roughness": 0.50, "metalness": 0.50},
    "fastener": {"name": "Plated fastener", "baseColor": "#DCDFE2", "roughness": 0.30, "metalness": 0.60},
    "copper": {"name": "Copper", "baseColor": "#C77B3B", "roughness": 0.35, "metalness": 0.60},
    "tube_bundle": {"name": "Brazed tube bundle", "baseColor": "#ABA398", "roughness": 0.46, "metalness": 0.50},
    "nozzle_alloy": {"name": "Nozzle sheet alloy", "baseColor": "#B9B5AF", "roughness": 0.36, "metalness": 0.60},
    "nozzle_oxide": {"name": "Oxidised nozzle alloy", "baseColor": "#8A9A84", "roughness": 0.50, "metalness": 0.40},
    "hot_alloy": {"name": "Hot-section alloy", "baseColor": "#9E968E", "roughness": 0.52, "metalness": 0.45},
    "brass": {"name": "Brass", "baseColor": "#C4A55C", "roughness": 0.36, "metalness": 0.60},
    "graphite": {"name": "Graphite", "baseColor": "#5F6269", "roughness": 0.70, "metalness": 0.10},
    "composite": {"name": "Wound composite", "baseColor": "#6A665B", "roughness": 0.60, "metalness": 0.05},
    "paint_grey": {"name": "Grey paint", "baseColor": "#CDD1D6", "roughness": 0.55, "metalness": 0.05},
    "paint_olive": {"name": "Olive paint", "baseColor": "#8C9A78", "roughness": 0.60, "metalness": 0.05},
    "radome": {"name": "Radome ceramic", "baseColor": "#E6E8EA", "roughness": 0.70, "metalness": 0.0},
    "ablative": {"name": "Ablative tip", "baseColor": "#C8603F", "roughness": 0.75, "metalness": 0.0},
    "propellant": {"name": "Propellant grain", "baseColor": "#BDA070", "roughness": 0.90, "metalness": 0.0},
    "inert": {"name": "Inert placeholder", "baseColor": "#A07474", "roughness": 0.75, "metalness": 0.0},
    "electronics": {"name": "Electronics housing", "baseColor": "#6F8A78", "roughness": 0.60, "metalness": 0.10},
    # heat tint, in the order the oxide colours appear with rising temperature
    "tint_straw": {"name": "Heat tint, straw", "baseColor": "#CDAA5A", "roughness": 0.36, "metalness": 0.55},
    "tint_bronze": {"name": "Heat tint, bronze", "baseColor": "#B0764A", "roughness": 0.36, "metalness": 0.55},
    "tint_purple": {"name": "Heat tint, purple", "baseColor": "#7E5A96", "roughness": 0.36, "metalness": 0.55},
    "tint_blue": {"name": "Heat tint, blue", "baseColor": "#5580B4", "roughness": 0.36, "metalness": 0.55},
}


def colour(finish):
    return FINISHES[finish]["baseColor"]


def materials(assigned):
    """`materials=` value for the cadgen decorators from {part label: finish id}."""
    used = sorted(set(assigned.values()))
    return {"definitions": {f: FINISHES[f] for f in used},
            "assignments": [{"targets": [f"#{label}" for label, g in assigned.items() if g == f], "material": f}
                            for f in used]}


# A model lists its parts as [(sub-assembly or None, part label, finish, ops)]; these turn that list into
# what assemble(), the native CAD builders and the cadgen decorators take.
def recipes(spec):
    """[(label, colour, ops)]"""
    return [(label, colour(finish), ops) for _, label, finish, ops in spec]


def groups(spec):
    """{sub-assembly: [part labels]} in the order the parts are listed."""
    out = {}
    for group, label, _, _ in spec:
        if group:
            out.setdefault(group, []).append(label)
    return out


def finishes(spec):
    """`materials=` value for the cadgen decorators."""
    return materials({label: finish for _, label, finish, _ in spec})
