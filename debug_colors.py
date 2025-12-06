import json

base_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot.json'
stardust_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot-stardust.json'

BLUE_SHELL = (0.286, 0.659, 1)

def find_blue(obj, path=""):
    found = []
    if isinstance(obj, dict):
        # Check Color 'c'
        if 'c' in obj and isinstance(obj['c'], dict) and 'k' in obj['c']:
            k = obj['c']['k']
            if isinstance(k, list) and len(k) >= 3 and isinstance(k[0], (int, float)):
                r, g, b = k[0], k[1], k[2]
                if abs(r - BLUE_SHELL[0]) < 0.05 and abs(g - BLUE_SHELL[1]) < 0.05 and abs(b - BLUE_SHELL[2]) < 0.05:
                    found.append(f"{path} -> Color c.k: ({r}, {g}, {b})")
        
        # Check Gradient 'g'
        if 'g' in obj and isinstance(obj['g'], dict) and 'k' in obj['g']:
            k = obj['g']['k']
             # Gradient usually has many numbers, check chunks
            if isinstance(k, list):
                i = 0
                while i < len(k) - 2:
                    if isinstance(k[i], (int, float)):
                        r, g, b = k[i], k[i+1], k[i+2]
                        if abs(r - BLUE_SHELL[0]) < 0.05 and abs(g - BLUE_SHELL[1]) < 0.05 and abs(b - BLUE_SHELL[2]) < 0.05:
                            found.append(f"{path} -> Gradient g.k: ({r}, {g}, {b})")
                        i += 1 # Check every offset just in case
                    else:
                        i+=1

        for key in obj:
            found.extend(find_blue(obj[key], f"{path}.{key}"))
            
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(find_blue(item, f"{path}[{idx}]"))
            
    return found

print("--- Checking Base robot.json ---")
try:
    with open(base_path, 'r') as f: data = json.load(f)
    results = find_blue(data)
    print(f"Found {len(results)} occurrences of Blue Shell.")
    # for r in results[:3]: print(r)
except: print("Error reading base")

print("\n--- Checking robot-meltdown.json ---")
meltdown_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot-meltdown.json'
try:
    with open(meltdown_path, 'r') as f: data = json.load(f)
    # Check if Blue Shell persists (Should be 0)
    results = find_blue(data)
    if results:
        print(f"FAILED: Found {len(results)} occurrences of Original Blue Shell in Meltdown file.")
    else:
        print("SUCCESS: Original Blue Shell is GONE in Meltdown file.")
        
    # Check if RED Shell exists ([0.86, 0.15, 0.15])
    RED_SHELL = (0.86, 0.15, 0.15)
    def find_red(obj):
        found = False
        if isinstance(obj, dict):
            if 'c' in obj and 'k' in obj['c']:
                k = obj['c']['k']
                if isinstance(k, list) and len(k) >= 3 and isinstance(k[0], (int, float)):
                    if abs(k[0] - RED_SHELL[0]) < 0.05: found = True
            for key in obj:
                if find_red(obj[key]): found = True
        elif isinstance(obj, list):
            for item in obj:
                if find_red(item): found = True
        return found
        
    if find_red(data):
        print("SUCCESS: Found RED Shell color in Meltdown file.")
    else:
        print("FAILED: Did NOT find RED Shell color in Meltdown file.")

except Exception as e: print(f"Error: {e}")
