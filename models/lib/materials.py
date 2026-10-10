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
    "hot_alloy": {"name": "Hot-section alloy", "baseColor": "#9E968E", "roughness": 0.52, "metalness": 0.45},
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
