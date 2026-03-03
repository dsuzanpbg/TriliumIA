#!/usr/bin/env python3
"""
=======================================
TUI - Interfaz de Usuario Textual
Version simplificada para Textual 8.x
=======================================
"""

import os
import sys

# Agregar lib al path
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(script_dir, "lib")
if os.path.exists(lib_dir):
    sys.path.insert(0, lib_dir)

# Importar Textual
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Vertical
    from textual.widgets import Header, Footer, Button, Static, SelectionList, Label, Tree, Input
    from textual.binding import Binding
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


# Importar modulos del proyecto
sys.path.insert(0, script_dir)
from core import ConfigManager
from adapters.asana import AsanaAdapter
from adapters.trilium import TriliumAdapter


# ========================================
# MAIN APP
# ========================================

class YamlImporterApp(App):
    """Aplicacion principal TUI"""

    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("escape", "quit", "Salir"),
    ]

    def __init__(self, config_file: str = "config.json", **kwargs):
        super().__init__(**kwargs)
        self.config_file = config_file
        self.selected_file: str = ""
        self.selected_destinations: list = []
        self.execute_mode: bool = False
        self.scope: str = "all"
        self.trilium_parent: str = ""
        self.update_existing: bool = False
        self.portfolio_gid: str = ""
        
        # Cargar configuracion
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.load()
        self.scope = getattr(self.config.defaults, "scope", "all")
        self.my_ids = getattr(self.config.defaults, "my_ids", []) or []
        self.trilium_parent = getattr(self.config.trilium, "parent_note_id", "") if hasattr(self.config, "trilium") else ""
        self.portfolio_gid = getattr(self.config.asana, "portfolio_gid", "") if hasattr(self.config, "asana") else ""
        
        # Buscar archivos YAML
        self.yaml_files = self._find_yaml_files()

    def _find_yaml_files(self) -> list:
        """Encontrar archivos YAML"""
        import glob
        patterns = ["*.yml", "*.yaml", "unorganizer/*.yml", "unorganizer/*.yaml"]
        yaml_files = set()
        for pattern in patterns:
            yaml_files.update(glob.glob(pattern, recursive=False))
        return sorted(yaml_files)

    def compose(self) -> ComposeResult:
        """Composicionar la UI"""
        yield Header()
        
        yield Container(
            Vertical(
                Static("YAML Importador", id="title"),
                Static("Importa tareas desde YAML a Asana o Trilium", id="subtitle"),
                Button("INICIAR", id="btn_start", variant="primary"),
                Button("SALIR", id="btn_quit", variant="default"),
                id="home"
            ),
            Container(
                Static("Seleccionar Archivo YAML", id="file_title"),
                SelectionList(id="file_list"),
                Static("", id="file_status"),
                Button("CONTINUAR", id="btn_file_next", variant="primary"),
                Button("ATRÁS", id="btn_file_back", variant="default"),
                id="files"
            ),
            Container(
                Static("Seleccionar Destino", id="dest_title"),
                Static("Elige a donde importar:", id="dest_label"),
                Button("Asana: SI", id="btn_asana", variant="primary"),
                Button("Trilium: NO", id="btn_trilium", variant="default"),
                Static("", id="dest_status"),
                Static("Trilium parent_note_id (opcional)", id="trilium_parent_label"),
                Input(placeholder="Ingresa parent_note_id", id="trilium_parent_input"),
                Button("CONTINUAR", id="btn_dest_next", variant="primary"),
                Button("ATRÁS", id="btn_dest_back", variant="default"),
                id="destination"
            ),
            Container(
                Static("Ver YAML", id="yaml_title"),
                Static("", id="yaml_info"),
                Tree("YAML", id="yaml_tree"),
                Static("", id="yaml_detail"),
                Button("EDITAR", id="btn_yaml_edit", variant="default"),
                Button("CONTINUAR", id="btn_yaml_next", variant="primary"),
                Button("ATRÁS", id="btn_yaml_back", variant="default"),
                id="yaml_view"
            ),
            Container(
                Static("Modo de Operacion", id="mode_title"),
                Button("Analisis (dry-run)", id="btn_analyze", variant="primary"),
                Button("Ejecutar", id="btn_execute", variant="default"),
                Static("", id="mode_status"),
                Static("Alcance", id="scope_title"),
                Button("Todo el proyecto", id="btn_scope_all", variant="primary"),
                Button("Solo mis tareas", id="btn_scope_mine", variant="default"),
                Static("Actualizacion", id="update_title"),
                Button("No actualizar", id="btn_update_off", variant="primary"),
                Button("Actualizar existentes", id="btn_update_on", variant="default"),
                Static("Portfolio (Asana)", id="portfolio_title"),
                Input(placeholder="Portfolio GID (opcional)", id="input_portfolio"),
                Button("INICIAR", id="btn_mode_start", variant="success"),
                Button("ATRÁS", id="btn_mode_back", variant="default"),
                id="mode"
            ),
            Container(
                Static("Procesando...", id="progress_title"),
                Static("", id="progress_msg"),
                Static("", id="progress_detail"),
                id="progress"
            ),
            Container(
                Static("Resultados", id="result_title"),
                Static("", id="result_content"),
                Button("NUEVO", id="btn_result_new", variant="primary"),
                Button("SALIR", id="btn_result_quit", variant="default"),
                id="result"
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Al iniciar"""
        self.show_screen("home")

    def show_screen(self, screen_name: str) -> None:
        """Mostrar una pantalla"""
        # Ocultar todos
        self.query_one("#home").display = False
        self.query_one("#files").display = False
        self.query_one("#yaml_view").display = False
        self.query_one("#destination").display = False
        self.query_one("#mode").display = False
        self.query_one("#progress").display = False
        self.query_one("#result").display = False
        
        # Mostrar el seleccionado
        self.query_one(f"#{screen_name}").display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Manejar clicks"""
        btn_id = event.button.id
        
        # Home
        if btn_id == "btn_start":
            if not self.yaml_files:
                self.query_one("#file_status", Static).update("No hay archivos YAML")
                return
            self.show_screen("files")
            # Poblar lista de archivos
            sl = self.query_one("#file_list", SelectionList)
            # SelectionList usa tuplas (label, value)
            sl.clear_options()
            for f in self.yaml_files:
                sl.add_option((f, f))
            if self.yaml_files:
                sl.select(0)
        
        elif btn_id == "btn_quit":
            self.exit()
        
        # Files
        elif btn_id == "btn_file_next":
            sl = self.query_one("#file_list", SelectionList)
            selected = sl.selected
            if selected:
                # selected es una lista de indices, obtener el valor
                idx = selected[0]
                opt = sl.get_option_at_index(idx)
                self.selected_file = opt.value
                # Mostrar pantalla de YAML
                self._load_yaml_tree()
                self.show_screen("yaml_view")
            else:
                self.query_one("#file_status", Static).update("Selecciona un archivo")
        
        elif btn_id == "btn_file_back":
            self.show_screen("home")
        
        # YAML View
        elif btn_id == "btn_yaml_next":
            self.show_screen("destination")
            # Prefill parent_note_id if available
            try:
                self.query_one("#trilium_parent_input", Input).value = self.trilium_parent or ""
            except Exception:
                pass

        elif btn_id == "btn_yaml_back":
            self.show_screen("files")
        
        elif btn_id == "btn_yaml_edit":
            self.query_one("#yaml_detail", Static).update("[yellow]Editor no implementado aun[/yellow]")
        
        # Destination
        elif btn_id == "btn_asana":
            if "asana" in self.selected_destinations:
                self.selected_destinations.remove("asana")
                event.button.label = "Asana: NO"
                event.button.variant = "default"
            else:
                self.selected_destinations.append("asana")
                event.button.label = "Asana: SI"
                event.button.variant = "primary"
        
        elif btn_id == "btn_trilium":
            if "trilium" in self.selected_destinations:
                self.selected_destinations.remove("trilium")
                event.button.label = "Trilium: NO"
                event.button.variant = "default"
            else:
                self.selected_destinations.append("trilium")
                event.button.label = "Trilium: SI"
                event.button.variant = "primary"
        
        elif btn_id == "btn_dest_next":
            if not self.selected_destinations:
                self.query_one("#dest_status", Static).update("Selecciona al menos un destino")
                return

            # parent_note_id para Trilium
            if "trilium" in self.selected_destinations:
                input_parent = self.query_one("#trilium_parent_input", Input).value.strip()
                if input_parent:
                    self.trilium_parent = input_parent
                if not self.trilium_parent:
                    self.query_one("#dest_status", Static).update("Ingresa parent_note_id para Trilium o configuralo en config.json")
                    return

            self.show_screen("mode")
        
        elif btn_id == "btn_dest_back":
            self.show_screen("files")
        
        # Mode
        elif btn_id == "btn_analyze":
            self.execute_mode = False
            self.query_one("#btn_analyze", Button).variant = "primary"
            self.query_one("#btn_execute", Button).variant = "default"
        
        elif btn_id == "btn_execute":
            self.execute_mode = True
            self.query_one("#btn_execute", Button).variant = "primary"
            self.query_one("#btn_analyze", Button).variant = "default"

        # Scope
        elif btn_id == "btn_scope_all":
            self.scope = "all"
            self.query_one("#btn_scope_all", Button).variant = "primary"
            self.query_one("#btn_scope_mine", Button).variant = "default"
        
        elif btn_id == "btn_scope_mine":
            self.scope = "mine"
            self.query_one("#btn_scope_mine", Button).variant = "primary"
            self.query_one("#btn_scope_all", Button).variant = "default"
        
        # Update mode
        elif btn_id == "btn_update_off":
            self.update_existing = False
            self.query_one("#btn_update_off", Button).variant = "primary"
            self.query_one("#btn_update_on", Button).variant = "default"
        
        elif btn_id == "btn_update_on":
            self.update_existing = True
            self.query_one("#btn_update_on", Button).variant = "primary"
            self.query_one("#btn_update_off", Button).variant = "default"
        
        elif btn_id == "btn_mode_start":
            self._run_sync()
        
        elif btn_id == "btn_mode_back":
            self.show_screen("destination")
        
        # Result
        elif btn_id == "btn_result_new":
            self.show_screen("home")
        
        elif btn_id == "btn_result_quit":
            self.exit()

    def _load_yaml_tree(self) -> None:
        """Cargar y mostrar el contenido del YAML en un Tree"""
        import yaml
        
        # Actualizar titulo con nombre del archivo
        self.query_one("#yaml_info", Static).update(f"Archivo: {self.selected_file}")
        
        # Cargar YAML
        tree = self.query_one("#yaml_tree", Tree)
        tree.clear()
        
        try:
            with open(self.selected_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                self.query_one("#yaml_detail", Static).update("El archivo esta vacio")
                return
            
            # Crear raiz del tree
            root = tree.root
            root.label = os.path.basename(self.selected_file).replace('.yml', '').replace('.yaml', '')
            
            # Obtener proyecto principal
            project_name = "PBG Microservices"
            project_desc = ""
            if 'project' in data:
                project_name = data['project'].get('name', project_name)
                project_desc = data['project'].get('description', '')
            
            # Obtener secciones
            sections_dict = {}
            if 'sections' in data and data['sections']:
                for s in data['sections']:
                    sections_dict[s.get('name', 'Sin nombre')] = s.get('description', '')
            
            # Obtener tareas por seccion
            tasks_by_section = {}
            if 'tasks' in data and data['tasks']:
                for task in data['tasks']:
                    task_name = task.get('name', 'Sin nombre')
                    task_section = task.get('section', '')
                    
                    if task_section:
                        if task_section not in tasks_by_section:
                            tasks_by_section[task_section] = []
                        tasks_by_section[task_section].append(task)
            
            # Crear estructura: Proyecto -> Secciones -> Tareas
            project_node = root.add(f"[PROYECTO] {project_name}")
            if project_desc:
                project_node.add(f"    {project_desc}")
            
            # Agregar secciones y sus tareas
            if sections_dict:
                for sec_name, sec_desc in sections_dict.items():
                    sec_node = project_node.add(f"[SECCION] {sec_name}")
                    if sec_desc:
                        sec_node.add(f"    {sec_desc}")
                    
                    # Agregar tareas de esta seccion
                    if sec_name in tasks_by_section:
                        tasks_node = sec_node.add(f"  Tareas ({len(tasks_by_section[sec_name])})")
                        for task in tasks_by_section[sec_name]:
                            task_name = task.get('name', 'Sin nombre')
                            task_due = task.get('due_date', '')
                            task_assignee = task.get('assignee', '')
                            
                            # Crear label de tarea
                            label = f"  {task_name}"
                            if task_due:
                                label += f" [{task_due}]"
                            if task_assignee:
                                label += f" (@{task_assignee})"
                            
                            task_node = tasks_node.add(label)
                            
                            # Agregar detalles
                            if task.get('notes'):
                                notes = task['notes'].strip()[:80]
                                task_node.add(f"    {notes}...")
            else:
                # Si no hay secciones, mostrar todas las tareas
                if tasks_by_section:
                    for sec_name, tasks in tasks_by_section.items():
                        sec_node = project_node.add(f"[SECCION] {sec_name}")
                        tasks_node = sec_node.add(f"  Tareas ({len(tasks)})")
                        for task in tasks:
                            task_node = tasks_node.add(f"  {task.get('name', 'Sin nombre')}")
            
            # Expandir raiz
            tree.expand(root)
            
            self.query_one("#yaml_detail", Static).update("[green]Navega con flechas, Enter para expandir[/green]")
            
        except Exception as e:
            self.query_one("#yaml_detail", Static).update(f"[red]Error: {str(e)}[/red]")

    def _add_yaml_nodes(self, parent_node, data, item_index: int = 0) -> None:
        """Agregar nodos al tree recursivamente"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)) and value:
                    child = parent_node.add(key)
                    self._add_yaml_nodes(child, value, item_index)
                else:
                    parent_node.add(f"{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    # Buscar campos importantes para mostrar como nombre
                    label = None
                    for field in ['name', 'title', 'label', 'id', 'key']:
                        if field in item:
                            label = f"{item[field]}"
                            break
                    
                    if label:
                        child = parent_node.add(label)
                    else:
                        child = parent_node.add(f"[{i + 1}]")
                    
                    self._add_yaml_nodes(child, item, i)
                elif isinstance(item, (dict, list)) and item:
                    child = parent_node.add(f"[{i + 1}]")
                    self._add_yaml_nodes(child, item, i)
                else:
                    parent_node.add(f"[{i + 1}]: {item}")

    def _run_sync(self) -> None:
        """Ejecutar la sincronizacion"""
        self.show_screen("progress")
        
        self.query_one("#progress_title", Static).update(f"Sincronizando a {', '.join(self.selected_destinations)}...")
        
        results = []
        
        for dest in self.selected_destinations:
            try:
                self.query_one("#progress_msg", Static).update(f"Procesando {dest}...")
                
                # Obtener portfolio_gid del input si existe
                portfolio_gid = ""
                try:
                    portfolio_input = self.query_one("#input_portfolio", Input)
                    if portfolio_input:
                        portfolio_gid = portfolio_input.value or self.portfolio_gid
                except:
                    portfolio_gid = self.portfolio_gid
                
                if dest == "asana":
                    adapter = AsanaAdapter({
                        "token": self.config.asana.token,
                        "workspace_gid": self.config.asana.workspace_gid,
                        "portfolio_gid": portfolio_gid,
                        "scope": self.scope,
                        "my_ids": self.my_ids
                    }, self.config.person_map)
                elif dest == "trilium":
                    parent_note = self.trilium_parent or self.config.trilium.parent_note_id
                    adapter = TriliumAdapter({
                        "etapi_token": self.config.trilium.etapi_token,
                        "base_url": self.config.trilium.base_url,
                        "parent_note_id": parent_note,
                        "scope": self.scope,
                        "my_ids": self.my_ids
                    }, self.config.person_map)
                    # Pasar flag de actualizacion
                    adapter.update_existing = self.update_existing
                else:
                    continue
                
                # Ejecutar
                if self.execute_mode:
                    state = adapter.execute(self.selected_file, dry_run=False)
                    mode = "EJECUTADO"
                else:
                    state = adapter.analyze(self.selected_file, dry_run=True)
                    mode = "ANALIZADO"
                
                results.append(f"=== {dest.upper()} ({mode}) ===")
                results.append(f"Proyectos: {len(state.projects)}")
                results.append(f"Secciones: {len(state.sections)}")
                results.append(f"Tareas: {len(state.tasks)}")
                results.append("")
                
            except Exception as e:
                results.append(f"ERROR en {dest}: {str(e)}")
        
        # Mostrar resultados
        result_text = "\n".join(results) if results else "Sin resultados"
        self.query_one("#result_content", Static).update(result_text)
        self.show_screen("result")


def run_tui(config_file: str = "config.json"):
    """Ejecutar la TUI"""
    if not TEXTUAL_AVAILABLE:
        print("Error: Textual no esta instalado")
        print("Ejecuta: pip install textual")
        return
    
    app = YamlImporterApp(config_file)
    app.run()


if __name__ == "__main__":
    run_tui()
