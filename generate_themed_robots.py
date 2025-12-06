import json
import os

base_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot.json'
output_dir = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets'

# Current Base Color (Cyberpunk Cyan - from previous edit): 
# #64ffda -> [0.3921, 1.0, 0.8549]

# Target Colors
themes = {
    'oceanic': [0.2196, 0.7411, 0.9725], # #38bdf8
    'stardust': [0.7529, 0.5176, 0.9882], # #c084fc
    'meltdown': [0.9843, 0.5725, 0.2353], # #fb923c
    'oceanic-light': [0.2196, 0.7411, 0.9725],
    'stardust-light': [0.7529, 0.5176, 0.9882],
    'meltdown-light': [0.9843, 0.5725, 0.2353]
}

def update_colors(obj, target_rgb):
    if isinstance(obj, dict):
        # Update Color Props "c": {"k": [r,g,b]}
        if 'c' in obj and isinstance(obj['c'], dict) and 'k' in obj['c'] and isinstance(obj['c']['k'], list):
            color = obj['c']['k']
            if len(color) >= 3 and isinstance(color[0], (int, float)):
                # Match the current base color (Cyan) with tolerance
                if abs(color[0] - 0.3921) < 0.05 and abs(color[1] - 1.0) < 0.05 and abs(color[2] - 0.8549) < 0.05:
                    obj['c']['k'][0] = target_rgb[0]
                    obj['c']['k'][1] = target_rgb[1]
                    obj['c']['k'][2] = target_rgb[2]
        
        # Update Gradient Props "g": {"k": [...]}
        if 'g' in obj and isinstance(obj['g'], dict) and 'k' in obj['g'] and isinstance(obj['g']['k'], list):
            grad = obj['g']['k']
            i = 0
            while i < len(grad) - 2:
                if isinstance(grad[i], (int, float)) and isinstance(grad[i+1], (int, float)) and isinstance(grad[i+2], (int, float)):
                     if abs(grad[i] - 0.3921) < 0.05 and abs(grad[i+1] - 1.0) < 0.05 and abs(grad[i+2] - 0.8549) < 0.05:
                        grad[i] = target_rgb[0]
                        grad[i+1] = target_rgb[1]
                        grad[i+2] = target_rgb[2]
                        i += 3
                     else:
                        i += 1
                else:
                    i += 1
                    
        for key in obj:
            update_colors(obj[key], target_rgb)
            
    elif isinstance(obj, list):
        for item in obj:
            update_colors(item, target_rgb)

try:
    with open(base_path, 'r', encoding='utf-8') as f:
        base_data = json.load(f)

    # Generate for unique colors (mapped by theme name)
    # We only need 3 files really: oceanic, stardust, meltdown
    # But for simplicity let's generate robot-themeName.json
    
    unique_themes = ['oceanic', 'stardust', 'meltdown'] # Light versions use same color
    
    for theme in unique_themes:
        import copy
        new_data = copy.deepcopy(base_data)
        target_rgb = themes[theme]
        
        update_colors(new_data, target_rgb)
        
        out_path = os.path.join(output_dir, f'robot-{theme}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, separators=(',', ':'))
            
        print(f"Generated {out_path}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
