#!/usr/bin/env python3
"""
========================================
ADAPTER - Trilium Notes (trilium-py)
========================================
"""

import sys
import os
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trilium_py.client import ETAPI
from core import Project, Section, Task, SyncStatus, SyncState


# ========================================
# CLI UI SIMPLE
# ========================================


class CLIUI:
    @staticmethod
    def info(msg):
        print(f"> {msg}")


CLIUI = CLIUI


# ========================================
# TRILIUM ADAPTER
# ========================================


class TriliumAdapter:
    """Adaptador para Trilium usando trilium-py"""

    name = "trilium"
    display_name = "Trilium Notes"

    def __init__(self, config: Dict, person_map: Dict[str, str] = None):
        self.etapi_token = config.get("etapi_token", "")
        self.base_url = config.get("base_url", "http://localhost:3784")
        self.parent_note_id = config.get("parent_note_id", "")
        self.scope = config.get("scope", "all")
        self.my_ids = config.get("my_ids", []) or []
        self.person_map = person_map or {}
        self.update_existing = False  # Flag para actualizar notas existentes

        self.client = ETAPI(self.base_url, self.etapi_token) if self.etapi_token else None

    # ------------------ helpers ------------------
    def _format_task_content(self, task_data: Dict) -> str:
        lines = ["# " + task_data.get("name", "")]

        notes = task_data.get("notes", "")
        if notes:
            lines.append(notes.strip())

        if task_data.get("assignee"):
            lines.append(f"\nAssignee: {task_data.get('assignee')}")
        if task_data.get("due_date"):
            lines.append(f"Due date: {task_data.get('due_date')}")

        return "\n\n".join(lines)

    def _should_include(self, task_data: Dict) -> bool:
        if self.scope == "mine" and self.my_ids:
            return task_data.get("assignee", "") in self.my_ids
        return True

    def _add_attribute(self, note_id: str, name: str, value: str):
        if not value:
            return
        if not self.client:
            return
        self.client.create_attribute(
            noteId=note_id,
            type="label",
            name=name,
            value=value,
            isInheritable=False,
        )

    def _find_note_by_title(self, parent_id: str, title: str) -> str | None:
        """Busca una nota por titulo bajo un padre. Retorna el noteId o None."""
        if not self.client:
            return None
        try:
            # Buscar notas con el titulo
            results = self.client.search_note(title)
            if results and results.get('results'):
                for note in results.get('results', []):
                    # Verificar si es hijo del parent_id (puede ser parentNoteId o parentNoteIds)
                    parent_ids = note.get('parentNoteIds', [note.get('parentNoteId')])
                    if parent_id in parent_ids:
                        return note.get('noteId')
            return None
        except Exception:
            return None

    def _update_note_content(self, note_id: str, content: str):
        """Actualiza el contenido de una nota"""
        if not note_id or not content or not self.client:
            return False
        try:
            self.client.update_note_content(note_id, content)
            return True
        except Exception as e:
            CLIUI.info(f"[WARN] Error actualizando contenido: {e}")
            return False

    def _update_note_title(self, note_id: str, title: str):
        """Actualiza el titulo de una nota"""
        if not note_id or not title or not self.client:
            return False
        try:
            self.client.patch_note(noteId=note_id, title=title)
            return True
        except Exception as e:
            CLIUI.info(f"[WARN] Error actualizando titulo: {e}")
            return False

    def _delete_attributes(self, note_id: str, attr_name: str):
        """Elimina atributos de una nota por nombre"""
        if not note_id or not attr_name or not self.client:
            return
        try:
            # Obtener atributos de la nota
            note = self.client.get_note(note_id)
            if note and note.get('attributes'):
                for attr in note.get('attributes', []):
                    if attr.get('name') == attr_name and attr.get('type') == 'label':
                        attr_id = attr.get('attributeId')
                        if attr_id:
                            self.client.delete_attribute(attr_id)
        except Exception:
            pass  # Silencioso si no existe

    # ------------------ public API ------------------
    def analyze(self, yaml_file: str, dry_run: bool = True) -> SyncState:
        from core import YAMLParser

        state = SyncState()
        data = YAMLParser.parse_file(yaml_file)

        project_data = data.get("project", {})
        project_name = project_data.get("name", "PBG Microservices")

        state.projects.append(Project(
            name=project_name,
            description=project_data.get("description", ""),
            status=SyncStatus.NEW
        ))

        for section_data in data.get("sections", []):
            name = section_data.get("name", "")
            if not name:
                continue
            state.sections.append(Section(name=name, project_gid="", status=SyncStatus.NEW))

        for task_data in data.get("tasks", []):
            if not self._should_include(task_data):
                continue
            name = task_data.get("name", "")
            if not name:
                continue
            state.tasks.append(Task(
                name=name,
                description=task_data.get("notes", ""),
                due_date=task_data.get("due_date", ""),
                assignee=task_data.get("assignee", ""),
                project=project_name,
                section=task_data.get("section", ""),
                sync_status=SyncStatus.NEW,
                raw_data=task_data
            ))

        return state

    def execute(self, yaml_file: str, dry_run: bool = True) -> SyncState:
        from core import YAMLParser

        state = SyncState()
        data = YAMLParser.parse_file(yaml_file)

        # validar parent_note_id
        if not dry_run:
            if not self.parent_note_id:
                raise Exception("Trilium parent_note_id no configurado")
            if not self.client:
                raise Exception("Trilium token no configurado")

        # No creamos carpeta raiz - el proyecto va directo bajo parent_note_id
        root_id = self.parent_note_id

        # proyecto - buscar si ya existe
        project_data = data.get("project", {})
        project_name = project_data.get("name", "PBG Microservices")
        project_desc = project_data.get("description", "")
        project_title = f"[PROYECTO] {project_name}"

        if dry_run:
            # Verificar si existiria
            existing_project_id = self._find_note_by_title(root_id, project_title) if not dry_run else None
            CLIUI.info(f"[DRY-RUN] Proyecto: {project_name}" + (" (ya existe)" if existing_project_id else ""))
            project_id = existing_project_id or f"DRY-PROJ-{project_name}"
        else:
            # Buscar si ya existe
            existing_project_id = self._find_note_by_title(root_id, project_title)
            if existing_project_id:
                if self.update_existing:
                    # Actualizar contenido
                    new_content = f"# {project_name}\n\n{project_desc}"
                    self._update_note_content(existing_project_id, new_content)
                    CLIUI.info(f"[UPDATE] Proyecto actualizado: {project_name}")
                    project_status = SyncStatus.EXISTS
                else:
                    CLIUI.info(f"[INFO] Proyecto ya existe: {project_name}")
                    project_status = SyncStatus.EXISTS
                project_id = existing_project_id
            else:
                note = self.client.create_note(root_id, project_title, type="text", content=f"# {project_name}\n\n{project_desc}")
                project_id = note.get("note", {}).get("noteId") if isinstance(note, dict) else None
                if project_id:
                    self._add_attribute(project_id, "project", project_name)
                project_status = SyncStatus.SYNCED

        state.projects.append(Project(name=project_name, gid=project_id, status=project_status if not dry_run else SyncStatus.NEW))

        # secciones - buscar si ya existen
        section_map: Dict[str, str] = {}
        for section_data in data.get("sections", []):
            name = section_data.get("name", "")
            if not name:
                continue
            section_title = f"[SECCION] {name}"
            
            if dry_run:
                existing_section_id = self._find_note_by_title(project_id, section_title) if project_id and not dry_run else None
                CLIUI.info(f"[DRY-RUN] Seccion: {name}" + (" (ya existe)" if existing_section_id else ""))
                section_id = existing_section_id or f"DRY-SEC-{name}"
            else:
                existing_section_id = self._find_note_by_title(project_id, section_title) if project_id else None
                if existing_section_id:
                    if self.update_existing:
                        # Actualizar contenido
                        self._update_note_content(existing_section_id, f"# {name}\n")
                        CLIUI.info(f"[UPDATE] Seccion actualizada: {name}")
                        section_status = SyncStatus.EXISTS
                    else:
                        CLIUI.info(f"[INFO] Seccion ya existe: {name}")
                        section_status = SyncStatus.EXISTS
                    section_id = existing_section_id
                else:
                    note = self.client.create_note(project_id, section_title, type="text", content=f"# {name}\n")
                    section_id = note.get("note", {}).get("noteId") if isinstance(note, dict) else None
                    if section_id:
                        self._add_attribute(section_id, "section", name)
                    section_status = SyncStatus.SYNCED
            section_map[name] = section_id
            state.sections.append(Section(name=name, project_gid=project_id, gid=section_id, status=section_status if not dry_run else SyncStatus.NEW))

        # tareas - buscar si ya existen
        for task_data in data.get("tasks", []):
            if not self._should_include(task_data):
                continue
            name = task_data.get("name", "")
            if not name:
                continue

            section_name = task_data.get("section", "")
            parent_id = section_map.get(section_name, project_id)

            content = self._format_task_content(task_data)
            task_title = f"[TODO] {name}"

            if dry_run:
                existing_task_id = self._find_note_by_title(parent_id, task_title) if parent_id and not dry_run else None
                CLIUI.info(f"[DRY-RUN] Tarea: {name}" + (" (ya existe)" if existing_task_id else ""))
                task_id = existing_task_id or f"DRY-TASK-{name}"
            else:
                existing_task_id = self._find_note_by_title(parent_id, task_title) if parent_id else None
                if existing_task_id:
                    if self.update_existing:
                        # Actualizar contenido
                        self._update_note_content(existing_task_id, content)
                        # Actualizar atributos - eliminar y recrear
                        self._delete_attributes(existing_task_id, "assignee")
                        self._delete_attributes(existing_task_id, "dueDate")
                        self._add_attribute(existing_task_id, "assignee", task_data.get("assignee", ""))
                        self._add_attribute(existing_task_id, "dueDate", task_data.get("due_date", ""))
                        CLIUI.info(f"[UPDATE] Tarea actualizada: {name}")
                        task_status = SyncStatus.EXISTS
                    else:
                        CLIUI.info(f"[INFO] Tarea ya existe: {name}")
                        task_status = SyncStatus.EXISTS
                    task_id = existing_task_id
                else:
                    note = self.client.create_note(parent_id, task_title, type="text", content=content)
                    task_id = note.get("note", {}).get("noteId") if isinstance(note, dict) else None
                    # atributos
                    if task_id:
                        self._add_attribute(task_id, "assignee", task_data.get("assignee", ""))
                        self._add_attribute(task_id, "dueDate", task_data.get("due_date", ""))
                    task_status = SyncStatus.SYNCED

            state.tasks.append(Task(
                name=name,
                gid=task_id,
                assignee=task_data.get("assignee", ""),
                project=project_name,
                section=section_name,
                sync_status=task_status if not dry_run else SyncStatus.NEW,
                raw_data=task_data
            ))

        return state
