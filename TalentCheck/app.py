import os
import sys
import json
from pathlib import Path
from typing import Dict, List

# Reconfigure stdout/stderr to UTF-8 to prevent UnicodeEncodeError on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure local imports work whether run as a script or a module
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from main import TalentCheck
    from models import CandidateProfile, Skill, SkillCategory
except ImportError:
    from TalentCheck.main import TalentCheck
    from TalentCheck.models import CandidateProfile, Skill, SkillCategory

# Import rich library for beautiful console rendering
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich import print as rprint
    from rich.align import Align
except ImportError:
    # Safe fallback if Rich is somehow not available
    class MockConsole:
        def print(self, *args, **kwargs):
            print(*args)
    Console = MockConsole
    Panel = lambda content, *args, **kwargs: content
    Table = lambda *args, **kwargs: None
    rprint = print

console = Console()

# Define sample profiles
def get_sample_profiles() -> Dict[str, CandidateProfile]:
    return {
        "1": CandidateProfile(
            name="John Doe",
            email="john.doe@stanford.edu",
            education="BS Computer Science, Stanford University",
            skills=[
                Skill(skill_name="Python", category_code=SkillCategory.CODING, confidence="high"),
                Skill(skill_name="JavaScript", category_code=SkillCategory.CODING, confidence="medium"),
                Skill(skill_name="Data Structures", category_code=SkillCategory.DSA, confidence="high"),
                Skill(skill_name="Algorithms", category_code=SkillCategory.DSA, confidence="medium"),
                Skill(skill_name="AWS Cloud", category_code=SkillCategory.CLOUD, confidence="medium"),
                Skill(skill_name="SQL", category_code=SkillCategory.SQL, confidence="high"),
                Skill(skill_name="React Frontend", category_code=SkillCategory.SWE, confidence="medium"),
            ],
            hackathons=["Stanford TreeHacks 2024", "Google Solution Challenge"],
            internships=["Software Engineer Intern @ Google", "Backend Intern @ Stripe"],
            certifications=["AWS Certified Developer Associate"],
            preferred_roles=["Backend Engineer", "Full Stack Developer"]
        ),
        "2": CandidateProfile(
            name="Jane Smith",
            email="jane.smith@nyu.edu",
            education="BA Economics & Minor in CS, NYU",
            skills=[
                Skill(skill_name="Excel Data Modeling", category_code=SkillCategory.OTHER, confidence="high"),
                Skill(skill_name="Basic SQL Queries", category_code=SkillCategory.SQL, confidence="medium"),
                Skill(skill_name="Python Scripting", category_code=SkillCategory.CODING, confidence="low"),
            ],
            hackathons=[],
            internships=["Data Analyst Intern @ Local Startup"],
            certifications=[],
            preferred_roles=["Junior Data Analyst", "Business Analyst"]
        ),
        "3": CandidateProfile(
            name="Alice Johnson",
            email="alice.j@mit.edu",
            education="MS in Artificial Intelligence, MIT",
            skills=[
                Skill(skill_name="PyTorch", category_code=SkillCategory.AI, confidence="high"),
                Skill(skill_name="TensorFlow", category_code=SkillCategory.AI, confidence="high"),
                Skill(skill_name="Python", category_code=SkillCategory.CODING, confidence="high"),
                Skill(skill_name="System Design", category_code=SkillCategory.SYSTEM_DESIGN, confidence="medium"),
                Skill(skill_name="Kubernetes", category_code=SkillCategory.SYSTEM_DESIGN, confidence="low"),
            ],
            hackathons=["MIT HackMIT Winner", "NVIDIA AI Hackathon"],
            internships=["Research Intern @ OpenAI", "AI Engineer Intern @ Meta"],
            certifications=["Google Professional Machine Learning Engineer"],
            preferred_roles=["Machine Learning Engineer", "AI Researcher"]
        )
    }

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner_text = Text("✨ TALENT CHECK INTEGRATION ENGINE ✨\n", style="bold cyan")
    banner_text.append("Assess Candidate Readiness and Bridge Skill Gaps", style="italic white")
    
    panel = Panel(
        Align.center(banner_text),
        border_style="cyan",
        padding=(1, 2),
        subtitle="v2.0 • Premium CLI Dashboard"
    )
    console.print(panel)

def get_visual_bar(level: int) -> str:
    """Generate a color-coded bar representing level 1-10."""
    filled = "■" * level
    empty = "░" * (10 - level)
    
    if level >= 8:
        color = "green"
    elif level >= 5:
        color = "yellow"
    else:
        color = "red"
        
    return f"[{color}]{filled}{empty}[/{color}] ({level}/10)"

def display_dashboard(result, candidate: CandidateProfile, engine: TalentCheck):
    print_header()
    
    # 1. Summary Cards
    status_colors = {
        "Ready": "bold green",
        "Almost Ready": "bold yellow",
        "Needs Work": "bold orange3",
        "Not Ready": "bold red"
    }
    status_style = status_colors.get(result.overall_readiness, "white")
    
    summary_text = Text()
    summary_text.append("Candidate: ", style="bold white")
    summary_text.append(f"{result.candidate_name}\n", style="cyan")
    summary_text.append("Education: ", style="bold white")
    summary_text.append(f"{candidate.education}\n", style="magenta")
    summary_text.append("Target Company: ", style="bold white")
    summary_text.append(f"{result.company}\n\n", style="yellow")
    summary_text.append(f"Readiness Score: ", style="bold white")
    summary_text.append(f"{result.readiness_score}/100\n", style="bold green" if result.readiness_score >= 80 else "bold yellow")
    summary_text.append(f"Overall Status: ", style="bold white")
    summary_text.append(f"{result.overall_readiness}", style=status_style)

    panel_summary = Panel(
        summary_text,
        title="[bold]Candidate Assessment Summary[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    # 2. Applied Experience & Certifications Boosts Card
    boosts_text = Text()
    
    # Check certifications
    cert_matches = []
    category_keywords = {
        "CLOUD": ["aws", "azure", "gcp", "cloud"],
        "CODING": ["python", "java", "c++", "javascript", "coding", "programmer"],
        "SQL": ["sql", "database", "postgres", "mysql", "oracle", "db"],
        "AI": ["ai", "machine learning", "ml", "tensorflow", "pytorch", "deep learning"],
        "SYSTEM_DESIGN": ["docker", "kubernetes", "devops", "system design", "architecture"],
        "DSA": ["data structures", "algorithms", "dsa"],
        "NETWORKING": ["network", "networking", "ccna"],
        "OS": ["linux", "unix", "windows", "operating system", "os"]
    }
    
    if candidate.certifications:
        for cert in candidate.certifications:
            matched_cats = []
            for cat, keywords in category_keywords.items():
                if any(kw in cert.lower() for kw in keywords):
                    matched_cats.append(cat)
            if matched_cats:
                cert_matches.append(f"• {cert} -> [green]+2 level boost[/green] to {', '.join(matched_cats)}")
            else:
                cert_matches.append(f"• {cert} (general verification)")
    
    if cert_matches:
        boosts_text.append("📜 Certifications Boosts:\n", style="bold magenta")
        for match in cert_matches:
            boosts_text.append(f"  {match}\n")
    else:
        boosts_text.append("📜 Certifications: None listed\n", style="bold white")
        
    # Check internships & hackathons
    boosts_text.append("\n💼 Experience Boosts:\n", style="bold magenta")
    if candidate.internships:
        intern_boost = min(10.0, len(candidate.internships) * 3.0)
        boosts_text.append(f"  • {len(candidate.internships)} Internship(s): ")
        boosts_text.append(f"[green]+{intern_boost}%[/green] overall score boost\n")
        for intern in candidate.internships:
            boosts_text.append(f"    - {intern}\n", style="dim white")
    else:
        boosts_text.append("  • Internships: None listed\n", style="dim white")
        
    if candidate.hackathons:
        hack_boost = min(5.0, len(candidate.hackathons) * 1.5)
        boosts_text.append(f"  • {len(candidate.hackathons)} Hackathon(s): ")
        boosts_text.append(f"[green]+{hack_boost}%[/green] overall score boost\n")
        for hack in candidate.hackathons:
            boosts_text.append(f"    - {hack}\n", style="dim white")
    else:
        boosts_text.append("  • Hackathons: None listed\n", style="dim white")

    panel_boosts = Panel(
        boosts_text,
        title="[bold]Applied Experience Boosts[/bold]",
        border_style="magenta",
        padding=(1, 2)
    )
    
    # Print panels side by side/sequentially
    console.print(panel_summary)
    console.print(panel_boosts)
    
    # 3. Gaps and Skill Comparison Table
    table = Table(title="[bold white]Detailed Skillset Analysis[/bold white]", show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Category", style="bold white", width=18)
    table.add_column("Required Level", justify="center", width=16)
    table.add_column("Candidate Level", justify="center", width=16)
    table.add_column("Status / Visual Bar", justify="left")

    # Mapping codes to friendly names
    cat_names = {
        "COD": "Coding (COD)",
        "DSA": "Data Structures (DSA)",
        "OOD": "Object Oriented (OOD)",
        "APTI": "Aptitude (APTI)",
        "COMM": "Communication (COMM)",
        "AI": "AI / ML (AI)",
        "CLOUD": "Cloud (CLOUD)",
        "SQL": "SQL & Databases (SQL)",
        "SWE": "Software Eng (SWE)",
        "SYSD": "System Design (SYSD)",
        "NETW": "Networking (NETW)",
        "OS": "Operating Systems (OS)",
        "OTHER": "Other Skills"
    }

    for gap in result.skillset_gap:
        name = cat_names.get(gap.category_code.value, gap.category_code.value)
        req_level = gap.required_level
        cand_level = gap.candidate_level
        
        if gap.gap:
            status_text = f"[bold red]❌ Gap (-{req_level - cand_level})[/bold red]"
        else:
            status_text = "[bold green]✅ Met[/bold green]"
            
        bar = get_visual_bar(cand_level)
        table.add_row(
            name,
            f"{req_level}/10",
            f"{cand_level}/10",
            f"{status_text}  {bar}"
        )
        
    console.print(table)
    
    # 4. Recommendations
    rec_text = Text()
    for rec in result.recommendations:
        if "Improve" in rec:
            rec_text.append(f"  • {rec}\n", style="bold yellow")
        else:
            rec_text.append(f"  • {rec}\n", style="bold green")
            
    panel_rec = Panel(
        rec_text,
        title="[bold yellow]Targeted Actionable Recommendations[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel_rec)
    console.print()

def main_cli():
    # Initialize Engine
    engine = TalentCheck(data_dir="./data")
    
    sample_profiles = get_sample_profiles()
    
    while True:
        print_header()
        
        # Candidate selection
        rprint("\n[bold cyan]Step 1: Select Candidate Profile[/bold cyan]")
        for num, prof in sample_profiles.items():
            rprint(f"  [bold green]{num}[/bold green]. {prof.name} ({prof.education})")
        rprint("  [bold green]4[/bold green]. Load Profile from Custom JSON File")
        rprint("  [bold green]5[/bold green]. Exit Dashboard")
        
        choice = Prompt.ask("\nChoose candidate profile", choices=["1", "2", "3", "4", "5"], default="1")
        
        if choice == "5":
            rprint("[bold cyan]Exiting engine. Goodbye![/bold cyan]")
            break
            
        candidate = None
        if choice in ["1", "2", "3"]:
            candidate = sample_profiles[choice]
        elif choice == "4":
            json_path = Prompt.ask("Enter path to candidate profile JSON file")
            if not Path(json_path).exists():
                rprint(f"[bold red]Error: File '{json_path}' not found.[/bold red]")
                console.input("\nPress Enter to continue...")
                continue
            try:
                candidate = engine.data_loader.load_profile_from_json(json_path)
            except Exception as e:
                rprint(f"[bold red]Error parsing JSON: {e}[/bold red]")
                console.input("\nPress Enter to continue...")
                continue
        
        # Company selection
        companies = engine.get_available_companies()
        rprint("\n[bold cyan]Step 2: Select Target Company[/bold cyan]")
        for idx, company in enumerate(companies, 1):
            rprint(f"  [bold green]{idx}[/bold green]. {company}")
            
        comp_choice = Prompt.ask("\nChoose target company", choices=[str(i) for i in range(1, len(companies) + 1)], default="1")
        target_company = companies[int(comp_choice) - 1]
        
        # Run Check
        with console.status("[bold green]Running TalentCheck Engine Matchers...[/bold green]"):
            try:
                result = engine.run_talent_check(candidate, target_company)
            except Exception as e:
                rprint(f"[bold red]Error running match engine: {e}[/bold red]")
                console.input("\nPress Enter to continue...")
                continue
                
        # Display Dashboard
        display_dashboard(result, candidate, engine)
        
        if not Confirm.ask("Would you like to perform another assessment?"):
            rprint("[bold cyan]Exiting engine. Goodbye![/bold cyan]")
            break

if __name__ == "__main__":
    try:
        main_cli()
    except KeyboardInterrupt:
        rprint("\n[bold red]Dashboard terminated by user. Goodbye![/bold red]")
