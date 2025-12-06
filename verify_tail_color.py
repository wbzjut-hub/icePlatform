import json

meltdown_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot-meltdown.json'

def find_tail_color(data):
    if 'layers' in data:
        for layer in data['layers']:
            if layer.get('nm') == 'tail':
                print("Found Layer 'tail'")
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
        color = find_tail_color(data)
        
        if color:
            r, g, b = color[0], color[1], color[2]
            print(f"  RGB: ({r}, {g}, {b})")
            
            # Check if it's still Dark Purple [0.278, 0.106, 0.314]
            if abs(r - 0.278) < 0.1:
                 print("  RESULT: Color is DARK PURPLE (Untouched)")
            else:
                 print("  RESULT: Color is CHANGED")

except Exception as e:
    print(e)
