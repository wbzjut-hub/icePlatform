import json
import os
import copy

base_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot.json'
output_dir = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets'

# Source Colors (From Analysis)
# 1. Face (Cyan): [0.392, 1.0, 0.855]
# 2. Shell (Blue): [0.286, 0.659, 1.0]

SOURCE_FACE = (0.392, 1.0, 0.855)
SOURCE_SHELL = (0.286, 0.659, 1.0)

# Theme Palettes
# Format: 'theme': {'face': [r,g,b], 'shell': [r,g,b]}
THEMES = {
    'oceanic': {
        'face': [0.22, 0.74, 0.97],  # #38bdf8 (Sky Blue)
        'shell': [0.11, 0.38, 0.94]  # #1c64f2 (Strong Blue)
    },
    'stardust': {
        'face': [0.75, 0.52, 0.99],  # #c084fc (Lavender)
        'shell': [0.45, 0.15, 0.75]  # #7226bf (Deep Violet)
    },
    'meltdown': {
        'face': [0.98, 0.57, 0.24],  # #fb923c (Orange)
        'shell': [0.85, 0.18, 0.18]  # #dc2626 (Fiery Red)
    }
}

def color_distance(c1, c2):
    return sum(abs(c1[i] - c2[i]) for i in range(3))

def update_colors_recursive(obj, palette):
    if isinstance(obj, dict):
        # Update "c" (Color)
        if 'c' in obj and isinstance(obj['c'], dict) and 'k' in obj['c']:
            k = obj['c']['k']
            if isinstance(k, list) and len(k) >= 3 and isinstance(k[0], (int, float)):
                # Check match
                current_rgb = (k[0], k[1], k[2])
                
                # Check Face
                if color_distance(current_rgb, SOURCE_FACE) < 0.1:
                    obj['c']['k'][0] = palette['face'][0]
                    obj['c']['k'][1] = palette['face'][1]
                    obj['c']['k'][2] = palette['face'][2]
                # Check Shell
                elif color_distance(current_rgb, SOURCE_SHELL) < 0.1:
                    obj['c']['k'][0] = palette['shell'][0]
                    obj['c']['k'][1] = palette['shell'][1]
                    obj['c']['k'][2] = palette['shell'][2]

        # Update "g" (Gradient)
        if 'g' in obj and isinstance(obj['g'], dict) and 'k' in obj['g']:
            grad = obj['g']['k']
            if isinstance(grad, list):
                i = 0
                while i < len(grad) - 2:
                    if isinstance(grad[i], (int, float)):
                         current_rgb = (grad[i], grad[i+1], grad[i+2])
                         
                         if color_distance(current_rgb, SOURCE_FACE) < 0.1:
                            grad[i] = palette['face'][0]
                            grad[i+1] = palette['face'][1]
                            grad[i+2] = palette['face'][2]
                            i += 3
                         elif color_distance(current_rgb, SOURCE_SHELL) < 0.1:
                            grad[i] = palette['shell'][0]
                            grad[i+1] = palette['shell'][1]
                            grad[i+2] = palette['shell'][2]
                            i += 3
                         else:
                            i += 1
                    else:
                        i += 1

        for key in obj:
            update_colors_recursive(obj[key], palette)
            
    elif isinstance(obj, list):
        for item in obj:
            update_colors_recursive(item, palette)

try:
    with open(base_path, 'r', encoding='utf-8') as f:
        base_data = json.load(f)

    for theme_name, palette in THEMES.items():
        new_data = copy.deepcopy(base_data)
        update_colors_recursive(new_data, palette)
        
        out_path = os.path.join(output_dir, f'robot-{theme_name}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, separators=(',', ':'))
            
        print(f"Generated {out_path}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
