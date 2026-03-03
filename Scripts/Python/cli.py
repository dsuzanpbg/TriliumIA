#!/usr/bin/env python3
"""
=======================================
CLI - Importador YAML -> Sistemas de Planeacion
Usando Click Framework + Textual TUI
=======================================
"""

import sys
import os

# Agregar lib al path
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(script_dir, "lib")
if os.path.exists(lib_dir):
    sys.path.insert(0, lib_dir)

# Importar Rich y Click
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

import click
import glob
from typing import List

# Importar modulos
sys.path.insert(0, script_dir)
from core import ConfigManager, SyncState, SyncStatus
from adapters.asana import AsanaAdapter
from adapters.trilium import TriliumAdapter

# ========================================
# ADAPTERS REGISTRY
# ========================================

ADAPTERS = {
    "asana": AsanaAdapter,
    "trilium": TriliumAdapter,
}

# ========================================
# UI HELPERS
# ========================================

def header(title: str):
    if RICH_AVAILABLE:
        console.print(Panel.fit(f"[bold cyan]{title}[/bold cyan]", border_style="cyan", box=box.DOUBLE))
    else:
        print("=" * 60)
        print(title)
        print("=" * 60)

def print_summary(state: SyncState, update_mode: bool = False):
    if not RICH_AVAILABLE:
        print(f"\nProyectos: {len(state.projects)} | Secciones: {len(state.sections)} | Tareas: {len(state.tasks)}")
        return
    
    if update_mode:
        table = Table(title="Resumen", box=box.ROUNDED)
        table.add_column("Elemento", style="cyan")
        table.add_column("Total", style="magenta", justify="center")
        table.add_column("Nuevos", style="green", justify="center")
        table.add_column("Actualizados", style="yellow", justify="center")
        
        new_projects = sum(1 for p in state.projects if p.status == SyncStatus.NEW)
        upd_projects = sum(1 for p in state.projects if p.status == SyncStatus.EXISTS)
        new_tasks = sum(1 for t in state.tasks if t.sync_status == SyncStatus.NEW)
        upd_tasks = sum(1 for t in state.tasks if t.sync_status == SyncStatus.EXISTS)
        new_sections = sum(1 for s in state.sections if s.status == SyncStatus.NEW)
        upd_sections = sum(1 for s in state.sections if s.status == SyncStatus.EXISTS)
        
        table.add_row("Proyectos", str(len(state.projects)), str(new_projects), str(upd_projects))
        table.add_row("Secciones", str(len(state.sections)), str(new_sections), str(upd_sections))
        table.add_row("Tareas", str(len(state.tasks)), str(new_tasks), str(upd_tasks))
    else:
        table = Table(title="Resumen", box=box.ROUNDED)
        table.add_column("Elemento", style="cyan")
        table.add_column("Total", style="magenta", justify="center")
        table.add_column("Nuevos", style="green", justify="center")
        
        new_projects = sum(1 for p in state.projects if p.status == SyncStatus.NEW)
        new_tasks = sum(1 for t in state.tasks if t.sync_status == SyncStatus.NEW)
        new_sections = sum(1 for s in state.sections if s.status == SyncStatus.NEW)
        
        table.add_row("Proyectos", str(len(state.projects)), str(new_projects))
        table.add_row("Secciones", str(len(state.sections)), str(new_sections))
        table.add_row("Tareas", str(len(state.tasks)), str(new_tasks))
    console.print(table)

def print_projects(state: SyncState):
    if not state.projects:
        return
        
    if not RICH_AVAILABLE:
        print("\n--- PROYECTOS ---")
        for p in state.projects:
            print(f"  - {p.name}")
        return
    
    table = Table(title="Proyectos", box=box.SIMPLE)
    table.add_column("Proyecto", style="white")
    
    for p in state.projects:
        table.add_row(p.name)
    console.print(table)

def print_tasks(state: SyncState):
    if not state.tasks:
        return
        
    if not RICH_AVAILABLE:
        print("\n--- TAREAS ---")
        for t in state.tasks:
            due = f" [due: {t.due_date}]" if t.due_date else ""
            print(f"  - {t.name}{due}")
        return
    
    table = Table(title="Tareas", box=box.SIMPLE)
    table.add_column("Tarea", style="white")
    table.add_column("Proyecto", style="blue", width=15)
    table.add_column("Fecha", style="yellow", width=12)
    
    for t in state.tasks:
        table.add_row(t.name[:50], t.project[:15], t.due_date or "-")
    console.print(table)

def print_warnings(state: SyncState):
    if not state.warnings:
        return
    
    if RICH_AVAILABLE:
        console.print("\n[bold yellow]Notas:[/bold yellow]")
        for w in state.warnings:
            console.print(f"  - {w}")
    else:
        print("\n--- NOTAS ---")
        for w in state.warnings:
            print(f"  - {w}")

# ========================================
# HELPERS
# ========================================

def find_yaml_files() -> List[str]:
    """Encontrar archivos YAML - busca en planning/projects primero"""
    # Primero buscar en planning/projects
    patterns = [
        "planning/projects/*.yml",
        "planning/projects/*.yaml",
        "unorganizer/*.yml",
        "unorganizer/*.yaml",
        "*.yml",
        "*.yaml"
    ]
    yaml_files = set()
    for pattern in patterns:
        yaml_files.update(glob.glob(pattern, recursive=False))
    return sorted(yaml_files)

def get_adapter(system: str, config, scope=None, my_ids=None, parent_note_id=None, portfolio_gid=None):
    """Obtener adapter segun el sistema"""
    adapter_class = ADAPTERS.get(system)
    if not adapter_class:
        return None
    
    # Use overrides or fall back to config
    actual_scope = scope if scope else getattr(config.defaults, "scope", "all")
    actual_my_ids = my_ids if my_ids else getattr(config.defaults, "my_ids", [])
    actual_parent = parent_note_id if parent_note_id else getattr(config.trilium, "parent_note_id", "") if system == "trilium" else ""
    actual_portfolio = portfolio_gid if portfolio_gid else getattr(config.asana, "portfolio_gid", "") if system == "asana" else ""
    actual_team = getattr(config.asana, "team_gid", "") if system == "asana" else ""
    
    if system == "asana":
        return adapter_class({
            "token": config.asana.token,
            "workspace_gid": config.asana.workspace_gid,
            "team_gid": actual_team,
            "portfolio_gid": actual_portfolio,
            "scope": actual_scope,
            "my_ids": actual_my_ids
        }, config.person_map)
    elif system == "trilium":
        return adapter_class({
            "etapi_token": config.trilium.etapi_token,
            "base_url": config.trilium.base_url,
            "parent_note_id": actual_parent,
            "scope": actual_scope,
            "my_ids": actual_my_ids
        }, config.person_map)
    return None

# ========================================
# COMANDOS CLI
# ========================================

@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx):
    """Importador YAML -> Sistemas de Planeacion"""
    # Si no se da ningun subcomando, ejecutar TUI
    if ctx.invoked_subcommand is None:
        from tui import run_tui
        run_tui("config.json")

@cli.command("interactive")
@click.option("--config", "-c", default="config.json", help="Archivo de configuracion")
def interactive(config):
    """Modo interactivo CLI (basico)"""
    run_interactive(config)

@cli.command("tui")
@click.option("--config", "-c", default="config.json", help="Archivo de configuracion")
def launch_tui(config):
    """Lanzar interfaz grafica de terminal (Textual)"""
    try:
        import sys
        print(f"Python: {sys.executable}")
        print(f"Python path: {sys.path[:3]}")
        
        from tui import run_tui, TEXTUAL_AVAILABLE
        print(f"TEXTUAL_AVAILABLE: {TEXTUAL_AVAILABLE}")
        
        run_tui(config)
    except ImportError as e:
        print(f"Error importando TUI: {e}")
    except Exception as e:
        print(f"Error: {e}")

@cli.command("list")
def list_systems():
    """Listar sistemas disponibles"""
    header("Sistemas Disponibles")
    
    if RICH_AVAILABLE:
        table = Table(box=box.SIMPLE)
        table.add_column("Comando", style="cyan")
        table.add_column("Sistema", style="white")
        
        for sys_id, adapter_class in ADAPTERS.items():
            table.add_row(sys_id, adapter_class.display_name)
        
        console.print(table)
        console.print("\n[dim]Uso: python cli.py asana --yaml tasks.yml[/dim]")
    else:
        print("\nSistemas disponibles:")
        for sys_id, adapter_class in ADAPTERS.items():
            print(f"  - {sys_id}: {adapter_class.display_name}")

@cli.command("asn")
@click.option("--yaml", "-y", help="Archivo YAML")
@click.option("--execute", "-e", is_flag=True, help="Ejecutar (sin dry-run)")
@click.option("--config", "-c", default="config.json", help="Archivo de configuracion")
@click.option("--scope", default=None, help="Scope: all | mine")
@click.option("--my-id", multiple=True, help="IDs propios (ej: P1)")
@click.option("--portfolio-gid", default=None, help="Portfolio GID de Asana (opcional)")
def asana(yaml, execute, config, scope, my_id, portfolio_gid):
    """Importar a Asana"""
    my_ids = list(my_id) if my_id else None
    run_import("asana", yaml, execute, config, scope=scope, my_ids=my_ids, portfolio_gid=portfolio_gid)

@cli.command("tri")
@click.option("--yaml", "-y", help="Archivo YAML")
@click.option("--execute", "-e", is_flag=True, help="Ejecutar (sin dry-run)")
@click.option("--config", "-c", default="config.json", help="Archivo de configuracion")
@click.option("--parent-note-id", default=None, help="parent_note_id para Trilium")
@click.option("--scope", default=None, help="Scope: all | mine")
@click.option("--my-id", multiple=True, help="IDs propios (ej: P1)")
@click.option("--update", "-u", is_flag=True, help="Actualizar notas existentes")
def trilium(yaml, execute, config, parent_note_id, scope, my_id, update):
    """Importar a Trilium Notes"""
    my_ids = list(my_id) if my_id else None
    run_import("trilium", yaml, execute, config, parent_note_id=parent_note_id, scope=scope, my_ids=my_ids, update=update)

@cli.command()
@click.argument("system")
@click.option("--yaml", "-y", help="Archivo YAML")
@click.option("--execute", "-e", is_flag=True, help="Ejecutar (sin dry-run)")
@click.option("--config", "-c", default="config.json", help="Archivo de configuracion")
@click.option("--parent-note-id", default=None, help="parent_note_id para Trilium")
@click.option("--scope", default=None, help="Scope: all | mine")
@click.option("--my-id", multiple=True, help="IDs propios (ej: P1)")
@click.option("--update", "-u", is_flag=True, help="Actualizar notas existentes")
@click.option("--portfolio-gid", default=None, help="Portfolio GID de Asana (opcional)")
def run(system, yaml, execute, config, parent_note_id, scope, my_id, update, portfolio_gid):
    """Importar planeacion YAML a un sistema"""
    my_ids = list(my_id) if my_id else None
    run_import(system, yaml, execute, config, parent_note_id=parent_note_id, scope=scope, my_ids=my_ids, update=update, portfolio_gid=portfolio_gid)

def run_import(system: str, yaml_file: str, execute: bool, config_file: str, parent_note_id: str = None, scope: str = None, my_ids: list = None, update: bool = False, portfolio_gid: str = None):
    """Ejecutar importacion"""
    
    # Cargar config
    config_manager = ConfigManager(config_file)
    config = config_manager.load()
    
    # Obtener adapter
    adapter = get_adapter(system, config, scope=scope, my_ids=my_ids, parent_note_id=parent_note_id, portfolio_gid=portfolio_gid)
    if not adapter:
        if RICH_AVAILABLE:
            console.print(f"[red]Sistema desconocido: {system}[/red]")
        else:
            print(f"Error: Sistema desconocido {system}")
        return
    
    # Pasar flag de update al adapter
    if hasattr(adapter, 'update_existing'):
        adapter.update_existing = update
    
    # Buscar archivo YAML
    if not yaml_file:
        yaml_files = find_yaml_files()
        if yaml_files:
            yaml_file = yaml_files[0]
            if RICH_AVAILABLE:
                console.print(f"[cyan]Usando: {yaml_file}[/cyan]")
            else:
                print(f"Usando: {yaml_file}")
        else:
            if RICH_AVAILABLE:
                console.print("[red]No se encontraron archivos YAML[/red]")
            else:
                print("Error: No se encontraron archivos YAML")
            return
    
    if not os.path.exists(yaml_file):
        if RICH_AVAILABLE:
            console.print(f"[red]Archivo no encontrado: {yaml_file}[/red]")
        else:
            print(f"Error: Archivo no encontrado: {yaml_file}")
        return
    
    # Titulo
    dry_run = not execute
    mode = "EJECUCION" if not dry_run else "ANALISIS"
    adapter_name = adapter.display_name
    header(f"YAML -> {adapter_name} | {mode}")
    
    if RICH_AVAILABLE:
        console.print(f"[dim]Archivo: {yaml_file}[/dim]")
        if not dry_run:
            console.print("[yellow]Se crearan elementos en el sistema![/yellow]\n")
        else:
            console.print("[dim]Modo analisis (dry-run)[/dim]\n")
    
    # Ejecutar
    try:
        import sys
        print(f"[CLI] Calling adapter.execute, dry_run={not execute}", flush=True)
        sys.stdout.flush()
        if dry_run:
            state = adapter.analyze(yaml_file, dry_run=True)
        else:
            state = adapter.execute(yaml_file, dry_run=False)
        print(f"[CLI] adapter.execute returned", flush=True)
        
        print_summary(state, update_mode=update)
        print_projects(state)
        print_tasks(state)
        print_warnings(state)
        
        if dry_run:
            if RICH_AVAILABLE:
                console.print(f"\n[bold]Para ejecutar:[/bold]")
                console.print(f"  [cyan]python cli.py {system} -y {yaml_file} --execute[/cyan]")
            else:
                print(f"\nPara ejecutar: python cli.py {system} -y {yaml_file} --execute")
                
    except Exception as e:
        import traceback
        print(f"Error: {e}", flush=True)
        traceback.print_exc()

# ========================================
# MODO INTERACTIVO
# ========================================

def run_interactive(config_file: str):
    """Modo interactivo con menus"""
    
    # Cargar config
    config_manager = ConfigManager(config_file)
    config = config_manager.load()
    
    if not RICH_AVAILABLE:
        print("Error: Se requiere Rich para modo interactivo")
        return
    
    # Banner inicial
    try:
        console.clear()
    except Exception:
        pass  # Si no se puede limpiar, continuar
    header("YAML Importador - Modo Interactivo")
    
    # 1. Seleccionar archivo YAML
    console.print("\n[bold yellow]Paso 1: Seleccionar archivo YAML[/bold yellow]\n")
    
    yaml_files = find_yaml_files()
    yaml_files.insert(0, "[Buscar archivo...]")
    
    for i, f in enumerate(yaml_files):
        console.print(f"  {i}. {f}")
    
    if not yaml_files[1:]:
        console.print("[yellow]No se encontraron archivos YAML en la carpeta[/yellow]")
        console.print("[dim]Puedes crear uno en la carpeta 'unorganizer/'[/dim]")
        return
    
    # Seleccionar archivo
    console.print()
    choice = click.prompt(
        "Selecciona archivo (numero)",
        type=click.IntRange(0, len(yaml_files) - 1),
        default=1 if len(yaml_files) > 1 else 0
    )
    
    if choice == 0:
        # Buscar archivo manualmente
        yaml_file = click.prompt("Ingresa la ruta del archivo YAML", type=str)
    else:
        yaml_file = yaml_files[choice]
    
    if not os.path.exists(yaml_file):
        console.print(f"[red]Archivo no encontrado: {yaml_file}[/red]")
        return
    
    console.print(f"[green]Archivo seleccionado: {yaml_file}[/green]\n")
    
    # 2. Seleccionar sistemas de destino
    console.print("[bold yellow]Paso 2: Seleccionar destino(s)[/bold yellow]\n")
    
    # Mostrar opciones
    console.print("  Sistemas disponibles:")
    for sys_id, adapter_class in ADAPTERS.items():
        status = "[green]OK[/green]" if sys_id in ["asana", "trilium"] else "[dim]proximamente[/dim]"
        console.print(f"    - {sys_id}: {adapter_class.display_name} {status}")
    
    console.print()
    
    # Preguntar por cada sistema
    targets = []
    
    # Asana
    console.print("[cyan]--- Asana ---[/cyan]")
    use_asana = click.confirm("Importar a Asana?", default=True)
    if use_asana:
        if config.asana.token and config.asana.workspace_gid:
            targets.append("asana")
            console.print("[green]  Asana habilitado[/green]")
        else:
            console.print("[red]  Token de Asana no configurado en config.json[/red]")
    
    # Trilium
    console.print("[cyan]--- Trilium ---[/cyan]")
    use_trilium = click.confirm("Importar a Trilium Notes?", default=True)
    if use_trilium:
        if config.trilium.etapi_token:
            targets.append("trilium")
            console.print("[green]  Trilium habilitado[/green]")
        else:
            console.print("[red]  Token de Trilium no configurado en config.json[/red]")
    
    if not targets:
        console.print("[red]No hay destinos habilitados[/red]")
        return
    
    console.print(f"\n[green]Destinos seleccionados: {', '.join(targets)}[/green]\n")
    
    # 3. Modo dry-run o ejecutar
    console.print("[bold yellow]Paso 3: Modo de operacion[/bold yellow]\n")
    console.print("  1. Analisis (dry-run) - Solo mostrar que se hara")
    console.print("  2. Ejecutar - Crear elementos en el sistema\n")
    
    mode = click.prompt("Selecciona modo", type=click.IntRange(1, 2), default=1)
    execute = (mode == 2)
    mode_name = "EJECUTAR" if execute else "ANALISIS"
    
    console.print(f"\n[bold]Modo: {mode_name}[/bold]\n")
    
    if not execute:
        console.print("[yellow]Solo se mostrara lo que se hara, no se creara nada.[/yellow]\n")
    
    # Confirmar
    console.print("[bold yellow]Confirmar?[/bold yellow]")
    confirm = click.confirm("Continuar?", default=True)
    if not confirm:
        console.print("[yellow]Operacion cancelada[/yellow]")
        return
    
    # Ejecutar para cada destino
    for system in targets:
        console.print()
        console.print(Panel.fit(f"[bold cyan]Sincronizando: {system.upper()}[/bold cyan]", border_style="cyan"))
        run_import(system, yaml_file, execute, config_file)

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    cli()
