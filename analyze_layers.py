import json

file_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot.json'

def get_colors_from_shapes(shapes, context=""):
    colors = []
    for shape in shapes:
        if 'ty' in shape:
            type_str = shape['ty']
            name = shape.get('nm', 'unnamed')
            
            # Fill (fl) or Stroke (st)
            if type_str == 'fl' or type_str == 'st':
                if 'c' in shape and 'k' in shape['c']:
                    k = shape['c']['k']
                    if isinstance(k, list) and len(k) >= 3 and isinstance(k[0], (int, float)):
                        r, g, b = round(k[0], 3), round(k[1], 3), round(k[2], 3)
                        colors.append(f"  Shape '{name}' ({type_str}) -> Color: ({r}, {g}, {b})")
            
            # Group (gr) -> Recursive
            if type_str == 'gr':
                if 'it' in shape:
                    colors.extend(get_colors_from_shapes(shape['it'], context + f" -> {name}"))
                    
    return colors

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'layers' in data:
        for layer in data['layers']:
            layer_name = layer.get('nm', 'Unnamed Layer')
            print(f"Layer: {layer_name}")
            
            if 'shapes' in layer:
                results = get_colors_from_shapes(layer['shapes'])
                for res in results:
                    print(res)
            elif 'ks' in layer:
                 # Check properties? usually shapes interact
                 pass
            print("-" * 20)

except Exception as e:
    import traceback
    traceback.print_exc()
