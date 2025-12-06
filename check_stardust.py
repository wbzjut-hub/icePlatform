import json

file_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot-stardust.json'

BLUE_SHELL = (0.286, 0.659, 1)

def check_color(obj):
    found = False
    if isinstance(obj, dict):
        if 'c' in obj and 'k' in obj['c']:
            k = obj['c']['k']
            if isinstance(k, list) and len(k) >= 3 and isinstance(k[0], (int, float)):
                r, g, b = k[0], k[1], k[2]
                # Check if it matches the original Blue Shell
                if abs(r - BLUE_SHELL[0]) < 0.05 and abs(g - BLUE_SHELL[1]) < 0.05 and abs(b - BLUE_SHELL[2]) < 0.05:
                    print(f"Found Original Blue Shell Color: ({r}, {g}, {b})")
                    found = True
        
        for key in obj:
            if check_color(obj[key]): found = True
            
    elif isinstance(obj, list):
        for item in obj:
             if check_color(item): found = True
             
    return found

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not check_color(data):
        print("Original Blue Shell Color NOT found (Update likely SUCCESSFUL or missed target).")
    else:
        print("Original Blue Shell Color STILL PRESENT (Update FAILED).")

except Exception as e:
    print(e)
