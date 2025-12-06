import json

meltdown_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot-meltdown.json'

def find_body_color(data):
    if 'layers' in data:
        for layer in data['layers']:
            if layer.get('nm') == 'body':
                print("Found Layer 'body'")
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
        color = find_body_color(data)
        
        if color:
            r, g, b = color[0], color[1], color[2]
            print(f"  RGB: ({r}, {g}, {b})")
            
            # Check against Meltdown Body [1.0, 0.93, 0.84] (Pale Orange)
            if abs(r - 1.0) < 0.1 and abs(g - 0.93) < 0.1 and abs(b - 0.84) < 0.1:
                 print("  RESULT: Color is PALE ORANGE (Correct for Meltdown Body)")
            elif r > 0.95 and g > 0.95 and b > 0.95:
                 print("  RESULT: Color is WHITE (Incorrect - Untinted)")
            else:
                 print("  RESULT: Color is UNKNOWN")
        else:
            print("  RESULT: Could not find body color")

except Exception as e:
    print(e)
