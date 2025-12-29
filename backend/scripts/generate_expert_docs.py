import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# App imports
# Add backend directory to sys.path to allow importing app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from app.db.session import SessionLocal
from app.models.workflow import Workflow

def generate_docs():
    output_dir = os.path.join(os.getcwd(), 'docs', 'experts')
    os.makedirs(output_dir, exist_ok=True)
    
    db = SessionLocal()
    try:
        # Fetch all workflows except system presets if needed, or just fetch all
        # We want the 21 think tank exeprts. 
        # filtering by those not "wf_agent" or "wf_general" or checking names?
        # The prompt says "Universal Think Tank", so we should probably fetch all content created by init script.
        # But user might have modified them.
        # Let's just fetch ALL workflows and filter by the known names or domains?
        # Or just export ALL workflows found in DB that look like experts.
        
        workflows = db.query(Workflow).all()
        
        # Expert Domains Keywords to identify Think Tank experts
        expert_keywords = [
            'Macro Strategist', 'Quant Analyst', 'Risk Manager', 'Crypto Native',
            'System Architect', 'Algo Geek', 'Security Spec Ops', 'Data Alchemist', 'DevOps Master',
            'Complex Systems Physicist', 'Evolutionary Biologist', 'Statistician',
            'Design Lead', 'Game Producer', 'Space Architect', 'User Researcher',
            'Historian', 'Behavioral Psychologist', 'Legal Counsel',
            'Product Visionary', 'Startup Founder'
        ]
        
        count = 0
        for wf in workflows:
            # Check if this workflow is one of our experts
            is_expert = any(k in wf.name for k in expert_keywords)
            
            if is_expert:
                # "Macro Strategist (宏观策略师)" -> "Macro_Strategist.md"
                safe_name = wf.name.split('(')[0].strip().replace(' ', '_')
                filename = f"{safe_name}.md"
                filepath = os.path.join(output_dir, filename)
                
                content = f"""# {wf.name}

## Description
{wf.description}

## System Prompt
```text
{wf.system_prompt}
```

## Tools
{', '.join(wf.tools_config) if wf.tools_config else 'None'}
"""
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Updated {filename}")
                count += 1
                
        print(f"Successfully updated {count} expert documents from database.")
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_docs()
