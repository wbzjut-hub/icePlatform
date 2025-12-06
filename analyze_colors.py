import json

file_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot.json'

def extract_colors(obj, colors_found):
    if isinstance(obj, dict):
        # Color property structure check
        if 'c' in obj and isinstance(obj['c'], dict) and 'k' in obj['c']:
            k = obj['c']['k']
            if isinstance(k, list) and len(k) >= 3 and isinstance(k[0], (int, float)):
                 # Round to 3 decimal places to group similar colors
                r, g, b = round(k[0], 3), round(k[1], 3), round(k[2], 3)
                color_tuple = (r, g, b)
                colors_found.add(color_tuple)
        
        # Check gradients "g": {"k": ...}
        if 'g' in obj and isinstance(obj['g'], dict) and 'k' in obj['g']:
            pass

        for key in obj:
            extract_colors(obj[key], colors_found)
    elif isinstance(obj, list):
        for item in obj:
            extract_colors(item, colors_found)

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    unique_colors = set()
    extract_colors(data, unique_colors)
    
    print("Found unique colors (R, G, B):")
    # Sort by brightness to guess what is what
    sorted_colors = sorted(list(unique_colors), key=lambda x: x[0]+x[1]+x[2])
    
    for c in sorted_colors:
        # Convert to 0-255 for easier identification
        r255, g255, b255 = int(c[0]*255), int(c[1]*255), int(c[2]*255)
        print(f"RGB: {c}  ->  [{r255}, {g255}, {b255}]")

except Exception as e:
    print(e)
