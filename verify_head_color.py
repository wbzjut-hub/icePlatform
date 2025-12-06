import json

meltdown_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot-meltdown.json'

def find_head_color(data):
    if 'layers' in data:
        for layer in data['layers']:
            if layer.get('nm') == 'head':
                print("Found Layer 'head'")
                if 'shapes' in layer:
                    def find_fill(shapes):
                        for shape in shapes:
                            if shape.get('nm') == 'Fill 1' and 'c' in shape:
                                return shape['c']['k']
                            if 'it' in shape: # Group
                                res = find_fill(shape['it'])
                                if res: return res
                        return None
                    
                    k = find_fill(layer['shapes'])
                    if k:
                         print(f"  Found 'Fill 1' Color: {k}")
                         return k
    return None

try:
    with open(meltdown_path, 'r') as f:
        data = json.load(f)
        color = find_head_color(data)
        
        if color:
            r, g, b = color[0], color[1], color[2]
            print(f"  RGB: ({r}, {g}, {b})")
            
            # Check against Red Shell [0.86, 0.15, 0.15]
            if abs(r - 0.86) < 0.1 and abs(g - 0.15) < 0.1:
                 print("  RESULT: Color is RED (Correct for Meltdown)")
            elif abs(r - 0.286) < 0.1:
                 print("  RESULT: Color is BLUE (Incorrect - Default)")
            elif abs(r - 0.45) < 0.1:
                 print("  RESULT: Color is PURPLE (Incorrect - Stardust?)")
            else:
                 print("  RESULT: Color is UNKNOWN")
        else:
            print("  RESULT: Could not find head color")

except Exception as e:
    print(e)
