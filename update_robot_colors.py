import json
import os

file_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot.json'

# Target Color (Old Blue): 20, 92, 158 -> [0.0784313725490196, 0.3607843137254902, 0.6196078431372549]
# New Color (Cyberpunk Cyan): 100, 255, 218 -> [0.39215686274509803, 1.0, 0.8549019607843137]

# We need to replace these float values in the JSON structure.
# Since JSON loads floats with varying precision, string replacement might be fragile.
# However, Lottie files usually keep original precision.
# Let's try to load as JSON, traverse and update "c.k" (color) and "g.k" (gradient) arrays.

def update_colors(obj):
    if isinstance(obj, dict):
        # Update Color Props "c": {"k": [r,g,b]}
        if 'c' in obj and isinstance(obj['c'], dict) and 'k' in obj['c'] and isinstance(obj['c']['k'], list):
            color = obj['c']['k']
            if len(color) >= 3 and isinstance(color[0], (int, float)):
                # Check for match with tolerance
                if abs(color[0] - 0.0784) < 0.05 and abs(color[1] - 0.3607) < 0.05 and abs(color[2] - 0.6196) < 0.05:
                    obj['c']['k'][0] = 0.3921
                    obj['c']['k'][1] = 1.0
                    obj['c']['k'][2] = 0.8549
        
        # Update Gradient Props "g": {"k": [...]}
        if 'g' in obj and isinstance(obj['g'], dict) and 'k' in obj['g'] and isinstance(obj['g']['k'], list):
            grad = obj['g']['k']
            i = 0
            while i < len(grad) - 2:
                if isinstance(grad[i], (int, float)) and isinstance(grad[i+1], (int, float)) and isinstance(grad[i+2], (int, float)):
                     if abs(grad[i] - 0.0784) < 0.05 and abs(grad[i+1] - 0.3607) < 0.05 and abs(grad[i+2] - 0.6196) < 0.05:
                        grad[i] = 0.3921
                        grad[i+1] = 1.0
                        grad[i+2] = 0.8549
                        i += 3
                     else:
                        i += 1
                else:
                    i += 1
                    
        for key in obj:
            update_colors(obj[key])
            
    elif isinstance(obj, list):
        for item in obj:
            update_colors(item)

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    update_colors(data)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':')) # Minify output
    
    print("Successfully updated robot.json colors.")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error updating JSON: {e}")
