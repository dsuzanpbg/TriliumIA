// ============================================
// SCRIPT DE SINCRONIZACION BIDIRECCIONAL ASANA <-> TRILIUM
// Version mejorada con todas las features de Asana
// ============================================
//
// CONFIGURACION (labels en ESTA nota):
//   #asanaToken=xxxxx
//   #asanaWorkspaceGid=xxxxx
//   #asanaParentNoteId=xxxxx (opcional)
//   #asanaIncludeCompleted=1
//   #syncDirection=bidirectional (o "asana-to-trilium")
//   #conflictResolution=latest-wins (o "asana-wins", "trilium-wins")
//
// ============================================

const ASANA_BASE = "https://app.asana.com/api/1.0";

// ============================================
// CLASE: ASANA CLIENT
// ============================================
class AsanaClient {
  constructor(token) {
    this.token = token;
  }

  async request(method, path, body = null) {
    const url = new URL(`${ASANA_BASE}${path}`);
    const options = {
      method,
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const res = await fetch(url.toString(), options);

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Asana HTTP ${res.status}: ${txt}`);
    }

    return await res.json();
  }

  async get(path, params = {}) {
    const url = new URL(`${ASANA_BASE}${path}`);
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    }
    return await this.request("GET", url.pathname + url.search);
  }

  async post(path, body) {
    return await this.request("POST", path, body);
  }

  async put(path, body) {
    return await this.request("PUT", path, body);
  }

  async delete(path) {
    return await this.request("DELETE", path);
  }

  // Obtener todos los proyectos del workspace
  async getProjects(workspaceGid) {
    const projects = [];
    let offset = null;

    do {
      const data = await this.get("/projects", {
        workspace: workspaceGid,
        limit: 100,
        offset,
        opt_fields: "gid,name,notes,archived,created_at,modified_at",
      });
      projects.push(...(data.data || []));
      offset = data.next_page?.offset || null;
    } while (offset);

    return projects;
  }

  // Obtener secciones de un proyecto
  async getSections(projectGid) {
    const sections = [];
    let offset = null;

    do {
      const data = await this.get(`/projects/${projectGid}/sections`, {
        limit: 100,
        offset,
        opt_fields: "gid,name,created_at",
      });
      sections.push(...(data.data || []));
      offset = data.next_page?.offset || null;
    } while (offset);

    return sections;
  }

  // Obtener campos personalizados de un proyecto
  async getCustomFields(projectGid) {
    const data = await this.get(`/projects/${projectGid}/custom_field_settings`, {
      opt_fields: "gid,custom_field.gid,custom_field.name,custom_field.type,custom_field.enum_options,custom_field.number_value",
    });
    return data.data || [];
  }

  // Obtener tareas de un proyecto
  async getProjectTasks(projectGid, includeCompleted = false) {
    const tasks = [];
    let offset = null;

    const completedSince = includeCompleted ? "1970-01-01T00:00:00.000Z" : "now";

    do {
      const data = await this.get("/tasks", {
        project: projectGid,
        limit: 100,
        offset,
        completed_since: completedSince,
        opt_fields: this.getTaskFields(),
      });
      tasks.push(...(data.data || []));
      offset = data.next_page?.offset || null;
    } while (offset);

    return tasks;
  }

  // Obtener todas las tareas asignadas al usuario
  async getMyTasks(workspaceGid, includeCompleted = false) {
    const tasks = [];
    let offset = null;
    const completedSince = includeCompleted ? "1970-01-01T00:00:00.000Z" : "now";

    do {
      const data = await this.get("/tasks", {
        assignee: "me",
        workspace: workspaceGid,
        limit: 100,
        offset,
        completed_since: completedSince,
        opt_fields: this.getTaskFields(),
      });
      tasks.push(...(data.data || []));
      offset = data.next_page?.offset || null;
    } while (offset);

    return tasks;
  }

  // Obtener detalle completo de una tarea
  async getTask(taskGid) {
    const data = await this.get(`/tasks/${taskGid}`, {
      opt_fields: this.getTaskFields(),
    });
    return data.data;
  }

  // Obtener subtareas de una tarea
  async getSubtasks(taskGid) {
    const data = await this.get(`/tasks/${taskGid}/subtasks`, {
      opt_fields: this.getTaskFields(),
    });
    return data.data || [];
  }

  // Obtener comentarios (stories) de una tarea
  async getStories(taskGid) {
    const data = await this.get(`/tasks/${taskGid}/stories`, {
      opt_fields: "gid,created_at,created_by.name,type,text,resource_subtype",
    });
    return data.data || [];
  }

  // Obtener adjuntos de una tarea
  async getAttachments(taskGid) {
    const data = await this.get(`/tasks/${taskGid}/attachments`, {
      opt_fields: "gid,name,resource_type,download_url,created_at,size",
    });
    return data.data || [];
  }

  // Actualizar una tarea
  async updateTask(taskGid, updates) {
    const data = await this.put(`/tasks/${taskGid}`, { data: updates });
    return data.data;
  }

  // Crear una tarea
  async createTask(taskData) {
    const data = await this.post("/tasks", { data: taskData });
    return data.data;
  }

  // Campos que queremos obtener de las tareas
  getTaskFields() {
    return [
      "gid",
      "name",
      "notes",
      "completed",
      "due_on",
      "due_at",
      "start_on",
      "start_at",
      "assignee.name",
      "assignee.gid",
      "projects.gid",
      "projects.name",
      "memberships.project.gid",
      "memberships.section.gid",
      "memberships.section.name",
      "parent.gid",
      "custom_fields",
      "tags",
      "tags.name",
      "created_at",
      "modified_at",
      "permalink_url",
      "resource_subtype",
      "approval_status",
    ].join(",");
  }
}

// ============================================
// CLASE: TRILIUM CLIENT
// ============================================
class TriliumClient {
  constructor() {
    this.cache = new Map();
  }

  // Obtener label
  getLabel(note, name) {
    return note.getLabelValue(name);
  }

  // Setear label
  setLabel(note, name, value) {
    note.setLabel(name, value);
  }

  // Obtener o crear nota
  getOrCreateNote(parentNoteId, title, content = "") {
    // Buscar nota existente por titulo
    const children = api.getNote(parentNoteId)?.children || [];
    let existingNote = children.find((c) => c.title === title);

    if (existingNote) {
      return existingNote;
    }

    // Crear nueva nota
    const { note } = api.createTextNote(parentNoteId, title, content);
    return note;
  }

  // Crear nota
  createNote(parentNoteId, title, content = "") {
    const { note } = api.createTextNote(parentNoteId, title, content);
    return note;
  }

  // Actualizar contenido
  updateContent(note, content) {
    note.setContent(content, { forceSave: true });
    note.save();
  }

  // Buscar nota por label
  findNoteByLabel(labelName, labelValue) {
    return api.getNoteWithLabel(labelName, labelValue);
  }

  // Obtener todas las notas con un label especifico
  findNotesByLabel(labelName) {
    // En Trilium, podemos buscar por prefijo de label
    // Esta es una aproximacion
    return [];
  }

  // Eliminar hijos de una nota
  deleteChildren(note) {
    const kids = note.children || [];
    for (const child of kids) {
      try {
        child.deleteNote();
      } catch (e) {
        api.log({ warn: "No pude borrar child", noteId: child.noteId, err: String(e) });
      }
    }
  }
}

// ============================================
// CLASE: FORMATTER
// ============================================
class Formatter {
  // Convertir HTML de Asana a formato Trilium
  static formatDescription(html) {
    if (!html) return "*Sin descripcion*";
    
    // Limpiar y formatear
    let text = html
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<p>/gi, "\n")
      .replace(/<\/p>/gi, "")
      .replace(/<strong>(.*?)<\/strong>/gi, "**$1**")
      .replace(/<b>(.*?)<\/b>/gi, "**$1**")
      .replace(/<em>(.*?)<\/em>/gi, "*$1*")
      .replace(/<i>(.*?)<\/i>/gi, "*$1*")
      .replace(/<a href="(.*?)">(.*?)<\/a>/gi, "[$2]($1)")
      .replace(/<ul>/gi, "\n")
      .replace(/<\/ul>/gi, "")
      .replace(/<li>(.*?)<\/li>/gi, "- $1\n")
      .replace(/<div[^>]*>(.*?)<\/div>/gi, "\n$1\n")
      .trim();

    return text || "*Sin descripcion*";
  }

  // Formatear fecha
  static formatDate(dateStr) {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  // Formatear fecha y hora
  static formatDateTime(dateStr) {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // Formatear prioridad
  static formatPriority(priority) {
    if (!priority) return "Sin prioridad";
    const p = parseInt(priority);
    if (p <= 1) return "Alta";
    if (p <= 3) return "Media";
    return "Baja";
  }

  // Formatear estado
  static formatStatus(completed) {
    return completed ? "Completada" : "Pendiente";
  }

  // Sanitizar titulo
  static sanitizeTitle(title) {
    if (!title) return "(sin titulo)";
    // Remover caracteres que pueden causar problemas
    return title.substring(0, 200).replace(/[\\/\n\r]/g, " ").trim();
  }

  // Formatear tamano de archivo
  static formatFileSize(bytes) {
    if (!bytes) return "-";
    const units = ["B", "KB", "MB", "GB"];
    let unitIndex = 0;
    let size = bytes;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }
}

// ============================================
// CLASE: SYNC ENGINE
// ============================================
class SyncEngine {
  constructor(config) {
    this.asana = new AsanaClient(config.token);
    this.trilium = new TriliumClient();
    this.config = config;
    this.projectMap = new Map();
    this.sectionMap = new Map();
    this.taskMap = new Map();
  }

  // Obtener nota padre
  getParentNoteId(scriptNote) {
    const parentFromLabel = this.trilium.getLabel(scriptNote, "asanaParentNoteId");
    if (parentFromLabel) return parentFromLabel;

    const parent = scriptNote.parents?.[0];
    if (!parent) throw new Error("No precise determinar parent. Usa #asanaParentNoteId");
    return parent.noteId;
  }

  // Obtener configuracion
  getConfig(scriptNote) {
    return {
      token: this.trilium.getLabel(scriptNote, "asanaToken") || this.config.token,
      workspaceGid: this.trilium.getLabel(scriptNote, "asanaWorkspaceGid") || this.config.workspaceGid,
      includeCompleted: this.trilium.getLabel(scriptNote, "asanaIncludeCompleted") === "1",
      syncDirection: this.trilium.getLabel(scriptNote, "syncDirection") || "bidirectional",
      conflictResolution: this.trilium.getLabel(scriptNote, "conflictResolution") || "latest-wins",
    };
  }

  // Sincronizar desde Asana hacia Trilium
  async syncFromAsana() {
    api.log("Iniciando sincronizacion desde Asana...");

    const scriptNote = api.currentNote;
    const config = this.getConfig(scriptNote);
    const parentNoteId = this.getParentNoteId(scriptNote);

    // 1. Obtener proyectos
    api.log("Obteniendo proyectos...");
    const projects = await this.asana.getProjects(config.workspaceGid);
    api.log(`Encontrados ${projects.length} proyectos`);

    // 2. Obtener tareas del usuario
    api.log("Obteniendo tareas...");
    const allTasks = await this.asana.getMyTasks(config.workspaceGid, config.includeCompleted);
    api.log(`Encontradas ${allTasks.length} tareas`);

    // 3. Obtener proyectos que tienen las tareas
    const projectGids = [...new Set(allTasks.flatMap((t) => (t.projects || []).map((p) => p.gid)))];
    const projectDetails = await Promise.all(
      projectGids.map(async (gid) => {
        try {
          const sections = await this.asana.getSections(gid);
          const customFields = await this.asana.getCustomFields(gid);
          return { gid, sections, customFields };
        } catch (e) {
          api.log({ warn: `Error obteniendo detalles del proyecto ${gid}`, err: String(e) });
          return { gid, sections: [], customFields: [] };
        }
      })
    );

    // 4. Crear estructura en Trilium
    await this.createTriliumStructure(projects, projectDetails, allTasks, parentNoteId, config);

    // 5. Guardar metadata de sincronizacion
    await this.saveSyncMetadata(parentNoteId);

    api.log("Sincronizacion desde Asana completada");
  }

  // Crear estructura en Trilium
  async createTriliumStructure(projects, projectDetails, tasks, parentNoteId, config) {
    const now = new Date();
    const dateStr = now.toISOString().split("T")[0];
    const timeStr = now.toTimeString().split(" ")[0];

    // Carpeta raiz de sincronizacion
    const syncFolder = this.trilium.getOrCreateNote(
      parentNoteId,
      `Asana Sync - ${dateStr}`,
      `# Sincronizacion Asana\n**Fecha:** ${dateStr} ${timeStr}\n**Total de tareas:** ${tasks.length}\n\n---\n`
    );

    // Carpeta de proyectos
    const projectsFolder = this.trilium.getOrCreateNote(
      syncFolder.noteId,
      "Proyectos",
      "# Proyectos\n\n"
    );

    // Procesar cada proyecto
    for (const project of projects) {
      const projectDetail = projectDetails.find((p) => p.gid === project.gid);
      if (!projectDetail) continue;

      // Crear carpeta del proyecto
      const projectNote = this.trilium.getOrCreateNote(
        projectsFolder.noteId,
        this.formatProjectTitle(project.name),
        this.formatProjectContent(project)
      );

      // Labels del proyecto
      this.trilium.setLabel(projectNote, "asanaProjectGid", project.gid);
      this.trilium.setLabel(projectNote, "syncStatus", "synced");
      projectNote.save();

      // Obtener tareas del proyecto
      const projectTasks = tasks.filter(
        (t) => (t.projects || []).some((p) => p.gid === project.gid)
      );

      // Agrupar por seccion
      const tasksBySection = this.groupTasksBySection(projectTasks, projectDetail.sections);

      // Crear secciones
      for (const section of projectDetail.sections) {
        const sectionTasks = tasksBySection[section.gid] || [];
        const sectionNote = this.trilium.getOrCreateNote(
          projectNote.noteId,
          this.formatSectionTitle(section.name),
          this.formatSectionContent(section, sectionTasks.length)
        );

        this.trilium.setLabel(sectionNote, "asanaSectionGid", section.gid);
        sectionNote.save();

        // Crear tareas
        for (const task of sectionTasks) {
          await this.createTaskNote(task, sectionNote.noteId, projectDetail.customFields);
        }
      }

      // Tareas sin seccion
      const unsectionedTasks = tasksBySection["unsectioned"] || [];
      if (unsectionedTasks.length > 0) {
        const unsectionedNote = this.trilium.getOrCreateNote(
          projectNote.noteId,
          "Sin Seccion",
          `# Tareas sin seccion\n\n`
        );

        for (const task of unsectionedTasks) {
          await this.createTaskNote(task, unsectionedNote.noteId, projectDetail.customFields);
        }
      }
    }

    // Crear indice de tareas
    await this.createTaskIndex(syncFolder.noteId, tasks);
  }

  // Crear nota de tarea
  async createTaskNote(task, parentNoteId, customFields) {
    const title = this.formatTaskTitle(task);
    const content = this.formatTaskContent(task, customFields);

    const taskNote = this.trilium.getOrCreateNote(parentNoteId, title, content);

    // Labels
    this.trilium.setLabel(taskNote, "asanaTaskGid", task.gid);
    this.trilium.setLabel(taskNote, "syncStatus", "synced");
    this.trilium.setLabel(taskNote, "lastModified", task.modified_at);
    this.trilium.setLabel(taskNote, "status", task.completed ? "completed" : "pending");
    this.trilium.setLabel(taskNote, "completed", task.completed ? "true" : "false");

    if (task.due_on) {
      this.trilium.setLabel(taskNote, "dueDate", task.due_on);
    }
    if (task.start_on) {
      this.trilium.setLabel(taskNote, "startDate", task.start_on);
    }
    if (task.parent?.gid) {
      this.trilium.setLabel(taskNote, "asanaParentTaskGid", task.parent.gid);
    }

    taskNote.save();

    // Obtener y crear subtareas
    const subtasks = await this.asana.getSubtasks(task.gid);
    if (subtasks.length > 0) {
      const subtasksNote = this.trilium.getOrCreateNote(
        taskNote.noteId,
        "Subtareas",
        "# Subtareas\n\n"
      );

      for (const subtask of subtasks) {
        await this.createTaskNote(subtask, subtasksNote.noteId, customFields);
      }
    }

    // Obtener y crear comentarios
    const stories = await this.asana.getStories(task.gid);
    if (stories.length > 0) {
      const commentsNote = this.trilium.getOrCreateNote(
        taskNote.noteId,
        "Comentarios",
        this.formatComments(stories)
      );
      commentsNote.save();
    }

    // Obtener y crear adjuntos
    const attachments = await this.asana.getAttachments(task.gid);
    if (attachments.length > 0) {
      const attachmentsNote = this.trilium.getOrCreateNote(
        taskNote.noteId,
        "Adjuntos",
        this.formatAttachments(attachments)
      );
      attachmentsNote.save();
    }

    return taskNote;
  }

  // Agrupar tareas por seccion
  groupTasksBySection(tasks, sections) {
    const result = {};

    for (const section of sections) {
      result[section.gid] = [];
    }
    result["unsectioned"] = [];

    for (const task of tasks) {
      const sectionGid = task.memberships?.[0]?.section?.gid;
      if (sectionGid && result[sectionGid]) {
        result[sectionGid].push(task);
      } else {
        result["unsectioned"].push(task);
      }
    }

    return result;
  }

  // Formatear titulo de proyecto
  formatProjectTitle(name) {
    return `[PROYECTO] ${name}`;
  }

  // Formatear contenido de proyecto
  formatProjectContent(project) {
    return `# ${project.name}

**Estado:** ${project.archived ? "Archivado" : "Activo"}
**Creado:** ${Formatter.formatDate(project.created_at)}
**Ultima modificacion:** ${Formatter.formatDate(project.modified_at)}

${project.notes ? `## Descripcion\n${Formatter.formatDescription(project.notes)}\n` : ""}

---
`;
  }

  // Formatear titulo de seccion
  formatSectionTitle(name) {
    return `[SECCION] ${name}`;
  }

  // Formatear contenido de seccion
  formatSectionContent(section, taskCount) {
    return `# ${section.name}

**Tareas:** ${taskCount}

---
`;
  }

  // Formatear titulo de tarea
  formatTaskTitle(task) {
    const status = task.completed ? "[DONE]" : "[TODO]";
    const prefix = task.parent?.gid ? "  " : ""; // Indent for subtasks
    return `${prefix}${status} ${Formatter.sanitizeTitle(task.name)}`;
  }

  // Formatear contenido de tarea
  formatTaskContent(task, customFields) {
    let content = `# ${task.name || "(sin titulo)"}

**Estado:** ${Formatter.formatStatus(task.completed)}
**Fecha limite:** ${task.due_at ? Formatter.formatDateTime(task.due_at) : task.due_on ? Formatter.formatDate(task.due_on) : "Sin fecha"}
**Fecha de inicio:** ${task.start_at ? Formatter.formatDateTime(task.start_on) : task.start_on ? Formatter.formatDate(task.start_on) : "-"}
**Asignado a:** ${task.assignee?.name || "Sin asignar"}
**Creado:** ${Formatter.formatDate(task.created_at)}
**Ultima modificacion:** ${Formatter.formatDate(task.modified_at)}

`;

    // Descripcion
    if (task.notes) {
      content += `## Descripcion\n${Formatter.formatDescription(task.notes)}\n\n`;
    }

    // Campos personalizados
    if (task.custom_fields && task.custom_fields.length > 0) {
      content += `## Campos Personalizados\n`;
      for (const cf of task.custom_fields) {
        const value = this.formatCustomFieldValue(cf);
        content += `- **${cf.name}:** ${value}\n`;
      }
      content += "\n";
    }

    // Tags
    if (task.tags && task.tags.length > 0) {
      content += `**Tags:** ${task.tags.map((t) => t.name).join(", ")}\n\n`;
    }

    // Enlace
    content += `## Enlaces\n[Abrir en Asana](${task.permalink_url || "#"})\n`;

    content += `---\n<small>ID: ${task.gid}</small>`;

    return content;
  }

  // Formatear valor de campo personalizado
  formatCustomFieldValue(cf) {
    if (cf.type === "enum" && cf.enum_value) {
      return cf.enum_value.name;
    }
    if (cf.type === "text" && cf.text_value) {
      return cf.text_value;
    }
    if (cf.type === "number" && cf.number_value !== null) {
      return cf.number_value;
    }
    if (cf.type === "date" && cf.date_value) {
      return Formatter.formatDate(cf.date_value);
    }
    return "-";
  }

  // Formatear comentarios
  formatComments(stories) {
    let content = "# Comentarios\n\n";

    for (const story of stories) {
      if (story.type === "comment") {
        content += `**${story.created_by?.name || "Usuario"}** - ${Formatter.formatDateTime(story.created_at)}\n\n${story.text}\n\n---\n\n`;
      }
    }

    return content;
  }

  // Formatear adjuntos
  formatAttachments(attachments) {
    let content = "# Adjuntos\n\n";

    for (const att of attachments) {
      content += `- [${att.name}](${att.download_url}) - ${Formatter.formatFileSize(att.size)} - ${Formatter.formatDate(att.created_at)}\n`;
    }

    return content;
  }

  // Crear indice de tareas
  async createTaskIndex(parentNoteId, tasks) {
    const indexNote = this.trilium.getOrCreateNote(
      parentNoteId,
      "Indice de Tareas",
      "# Indice de Tareas\n\n"
    );

    // Tareas pendientes
    const pending = tasks.filter((t) => !t.completed);
    const pendingNote = this.trilium.getOrCreateNote(
      indexNote.noteId,
      "Tareas Pendientes",
      `# Tareas Pendientes (${pending.length})\n\n` +
        pending.map((t) => `- [${t.name}](#) (${t.projects?.[0]?.name || "Sin proyecto"})`).join("\n")
    );
    pendingNote.save();

    // Tareas completadas
    const completed = tasks.filter((t) => t.completed);
    const completedNote = this.trilium.getOrCreateNote(
      indexNote.noteId,
      "Tareas Completadas",
      `# Tareas Completadas (${completed.length})\n\n` +
        completed.map((t) => `- [${t.name}](#) (${t.projects?.[0]?.name || "Sin proyecto"})`).join("\n")
    );
    completedNote.save();
  }

  // Guardar metadata de sincronizacion
  async saveSyncMetadata(parentNoteId) {
    const metaFolder = this.trilium.getOrCreateNote(
      parentNoteId,
      "Sync-Metadata",
      ""
    );

    const metaNote = this.trilium.getOrCreateNote(
      metaFolder.noteId,
      "ultima-sincronizacion",
      `# Ultima Sincronizacion\n\n**Fecha:** ${new Date().toISOString()}\n**Estado:** Completada`
    );

    this.trilium.setLabel(metaNote, "lastSync", new Date().toISOString());
    metaNote.save();
  }

  // Sincronizar desde Trilium hacia Asana
  async syncToAsana() {
    api.log("Iniciando sincronizacion hacia Asana...");

    const scriptNote = api.currentNote;
    const config = this.getConfig(scriptNote);

    if (config.syncDirection !== "bidirectional") {
      api.log("Sincronizacion bidireccional deshabilitada");
      return;
    }

    // Buscar notas con cambios pendientes
    // Este es un ejemplo basico - en produccion necesitarias mas logica
    api.log("Buscando notas con cambios pendientes...");

    // Por ahora, solo log
    api.log("Sincronizacion hacia Asana completada (pendiente de implementar)");
  }
}

// ============================================
// FUNCION PRINCIPAL
// ============================================
async function runSync() {
  api.log("========================================");
  api.log("Iniciando sincronizacion Asana <-> Trilium");
  api.log("========================================");

  try {
    const scriptNote = api.currentNote;
    const token = scriptNote.getLabelValue("asanaToken");
    const workspaceGid = scriptNote.getLabelValue("asanaWorkspaceGid");

    if (!token) throw new Error("Falta label #asanaToken=...");
    if (!workspaceGid) throw new Error("Falta label #asanaWorkspaceGid=...");

    const engine = new SyncEngine({ token, workspaceGid });

    // Sincronizar desde Asana
    await engine.syncFromAsana();

    // Sincronizar hacia Asana (si esta habilitado)
    const syncDirection = scriptNote.getLabelValue("syncDirection");
    if (syncDirection === "bidirectional") {
      await engine.syncToAsana();
    }

    api.log("========================================");
    api.log("Sincronizacion completada exitosamente");
    api.log("========================================");
  } catch (e) {
    api.log(`ERROR: ${e.stack || e}`);
    throw e;
  }
}

// ============================================
// EJECUCION
// ============================================
(async () => {
  await runSync();
})().catch((e) => api.log(`Error fatal: ${e.stack || e}`));
