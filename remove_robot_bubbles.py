import json

file_path = '/Users/wangbo/Desktop/Object/aiTalking/my-vue-app/src/assets/robot.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'layers' in data:
        original_count = len(data['layers'])
        # Filter out layers that contain "chat" in their name
        data['layers'] = [layer for layer in data['layers'] if 'nm' in layer and 'chat' not in layer['nm'].lower()]
        new_count = len(data['layers'])
        
        print(f"Removed {original_count - new_count} layers.")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
            
        print("Successfully removed chat bubbles from robot.json")
    else:
        print("No 'layers' key found in JSON.")

except Exception as e:
    print(f"Error: {e}")
