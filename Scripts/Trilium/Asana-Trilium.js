// ============================================
// SCRIPT DE SINCRONIZACIÓN ASANA → TRILIUM
// Trae tareas asignadas a ti (assignee=me)
// ============================================
//
//   #asanaToken="2/1212819181980643/1213035096329320:7864bbd04ceea846205e323dd5a631e0" 
//   #asanaWorkspaceGid=1111569889778748
// REQUERIDOS (labels en ESTA nota):
//   #asanaToken=xxxxx
//   #asanaWorkspaceGid=1111569889778748
//
// OPCIONALES:
//   #asanaParentNoteId=<noteId donde crear la estructura>
//   #asanaIncludeCompleted=1   (incluye completadas "desde siempre"; puede ser MUCHO)
//
// ============================================

const ASANA_BASE = "https://app.asana.com/api/1.0";

// ---------- Helpers Trilium (labels/config) ----------
function lbl(note, name) {
  return note.getLabelValue(name); // BNote.getLabelValue() :contentReference[oaicite:4]{index=4}
}
function lblOrThrow(note, name) {
  const v = lbl(note, name);
  if (!v) throw new Error(`Falta label #${name}=... en la nota del script`);
  return v;
}

function getParentNoteId(scriptNote) {
  const parentFromLabel = lbl(scriptNote, "asanaParentNoteId");
  if (parentFromLabel) return parentFromLabel;

  const parent = (scriptNote.parents && scriptNote.parents[0]) ? scriptNote.parents[0] : null;
  if (!parent) throw new Error("No pude determinar parent. Usa #asanaParentNoteId=<noteId>.");
  return parent.noteId;
}

// ---------- Asana HTTP ----------
async function asanaGet(token, path, paramsObj = {}) {
  const url = new URL(`${ASANA_BASE}${path}`);
  for (const [k, v] of Object.entries(paramsObj)) {
    if (v === undefined || v === null || v === "") continue;
    url.searchParams.set(k, String(v));
  }

  const res = await fetch(url.toString(), {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Asana HTTP ${res.status}: ${txt}`);
  }
  return await res.json();
}

// ============================================
// 1. FUNCIÓN PRINCIPAL DE SINCRONIZACIÓN
// ============================================
async function syncAllAsanaTasks() {
  api.log("🔄 Iniciando sincronización con Asana...");

  const scriptNote = api.currentNote; // Api.currentNote :contentReference[oaicite:5]{index=5}
  const token = lblOrThrow(scriptNote, "asanaToken");
  const workspaceGid = lblOrThrow(scriptNote, "asanaWorkspaceGid");
  const includeCompleted = lbl(scriptNote, "asanaIncludeCompleted") === "1";

  // 1) Traer tasks
  const allTasks = await getAllMyTasks({ token, workspaceGid, includeCompleted });
  api.log(`📊 Encontradas ${allTasks.length} tareas`);

  // 2) Crear estructura en Trilium
  const parentNoteId = getParentNoteId(scriptNote);
  await createTriliumStructure(allTasks, { parentNoteId });

  api.log("✅ Sincronización completada");
}

// ============================================
// 2. OBTENER TODAS LAS TAREAS ASIGNADAS
// ============================================
//
// Asana recomienda assignee=me + workspace=WORKSPACE_GID para “mis tareas del workspace”. :contentReference[oaicite:6]{index=6}
// Paginación: next_page.offset :contentReference[oaicite:7]{index=7}
//
async function getAllMyTasks({ token, workspaceGid, includeCompleted }) {
  const allTasks = [];
  let offset = null;

  // opt_fields: ver Input/Output options :contentReference[oaicite:8]{index=8}
  const opt_fields = [
    "gid",
    "name",
    "notes",
    "completed",
    "due_on",
    "due_at",
    "permalink_url",
    "created_at",
    "modified_at",
    "assignee.name",
    "projects.name",
  ].join(",");

  // Importante:
  // - completed_since=now => típicamente te regresa incompletas (útil para “pendientes”) :contentReference[oaicite:9]{index=9}
  // - si quieres incluir completadas, puedes dar una fecha antigua (ojo: puede ser muchísimo)
  const completed_since = includeCompleted ? "1970-01-01T00:00:00.000Z" : "now";

  do {
    const params = {
      assignee: "me",
      workspace: workspaceGid,
      limit: 100,
      offset: offset || undefined,
      opt_fields,
      completed_since,
    };

    const data = await asanaGet(token, "/tasks", params);

    allTasks.push(...(data.data || []));
    offset = data.next_page?.offset || null;
    api.log(`📥 Obtenidas ${data.data?.length || 0} tareas, offset: ${offset}`);
  } while (offset);

  return allTasks;
}

// ============================================
// 3. CREAR / RE-USAR “SYNC NOTE” (1 por día)
// ============================================
function getTodayStr() {
  return new Date().toISOString().split("T")[0];
}

function upsertSyncRoot(parentNoteId) {
  const today = getTodayStr();

  // Usamos un label para encontrar “la sync de hoy” sin depender de queries de búsqueda
  const existing = api.getNoteWithLabel("asanaSyncDate", today); // Api.getNoteWithLabel :contentReference[oaicite:10]{index=10}
  if (existing) return existing;

  const { note } = api.createTextNote(parentNoteId, `🔄 Asana Sync - ${today}`, ""); // createTextNote :contentReference[oaicite:11]{index=11}
  note.setLabel("asanaSyncDate", today); // setLabel :contentReference[oaicite:12]{index=12}
  note.save();
  return note;
}

function deleteAllChildren(note) {
  // BNote.children es accesible :contentReference[oaicite:13]{index=13}
  const kids = note.children || [];
  for (const child of kids) {
    try {
      child.deleteNote();
    } catch (e) {
      api.log({ warn: "No pude borrar child", noteId: child.noteId, err: String(e) });
    }
  }
}

// ============================================
// 4. CREAR ESTRUCTURA EN TRILIUM
// ============================================
async function createTriliumStructure(tasks, { parentNoteId }) {
  const now = new Date();
  const dateStr = now.toISOString().split("T")[0];
  const timeStr = now.toTimeString().split(" ")[0];

  const syncNote = upsertSyncRoot(parentNoteId);

  // “Reset” del día: borra sub-notas y reescribe contenido
  deleteAllChildren(syncNote);

  const pendingTasks = tasks.filter((t) => !t.completed);
  const completedTasks = tasks.filter((t) => t.completed);

  const header = `
# Sincronización Asana
**Fecha:** ${dateStr} ${timeStr}
**Total de tareas:** ${tasks.length}
**Tareas pendientes:** ${pendingTasks.length}
**Tareas completadas:** ${completedTasks.length}

---
`.trim();

  syncNote.setContent(header, { forceSave: true }); // setContent(forceSave) :contentReference[oaicite:14]{index=14}

  // Secciones
  if (pendingTasks.length) {
    const { note: pendingNote } = api.createTextNote(syncNote.noteId, "⏳ Tareas Pendientes", "");
    await processTaskGroup(pendingTasks, pendingNote.noteId, true);
  }

  if (completedTasks.length) {
    const { note: completedNote } = api.createTextNote(syncNote.noteId, "✅ Tareas Completadas", "");
    await processTaskGroup(completedTasks, completedNote.noteId, false);
  }

  await createProjectIndex(tasks, syncNote.noteId);
  await createKanbanView(tasks, syncNote.noteId);
}

// ============================================
// 5. PROCESAR GRUPO DE TAREAS
// ============================================
async function processTaskGroup(tasks, parentNoteId, showUrgency = true) {
  const sorted = [...tasks].sort((a, b) => {
    const aDue = a.due_at || a.due_on;
    const bDue = b.due_at || b.due_on;

    if (aDue && !bDue) return -1;
    if (!aDue && bDue) return 1;
    if (aDue && bDue) return new Date(aDue) - new Date(bDue);

    return new Date(b.modified_at || 0) - new Date(a.modified_at || 0);
  });

  for (const task of sorted) {
    await createTaskNote(task, parentNoteId, showUrgency);
  }
}

// ============================================
// 6. CREAR NOTA INDIVIDUAL DE TAREA
// ============================================
async function createTaskNote(task, parentNoteId, showUrgency = true) {
  const urgency = calculateUrgency(task.due_on || task.due_at);
  const urgencyIcon = showUrgency ? getUrgencyIcon(urgency) : "";
  const completedIcon = task.completed ? "✅" : "⏳";

  const safeTitle = (task.name || "(sin título)").substring(0, 100);
  const title = `${completedIcon} ${urgencyIcon} ${safeTitle}`.trim();

  const dueTxt = task.due_at || task.due_on || "Sin fecha";
  const projectsTxt =
    (task.projects && task.projects.length)
      ? task.projects.map((p) => p.name).filter(Boolean).join(", ")
      : "Sin proyecto";

  const content = `
# ${task.name || "(sin título)"}

**Estado:**<br/> ${task.completed ? "✅ Completada" : "⏳ Pendiente"}
**Fecha límite:**<br/> ${dueTxt} ${showUrgency ? getUrgencyBadge(urgency) : ""}
**Proyectos:**<br/> ${projectsTxt}
**Creada:**<br/> ${task.created_at ? new Date(task.created_at).toLocaleDateString() : "-"}
**Modificada:**<br/> ${task.modified_at ? new Date(task.modified_at).toLocaleDateString() : "-"}

## Enlaces<br/>
🔗 ${task.permalink_url ? task.permalink_url : "(sin link)"}

## Descripción<br/>
${task.notes || "*Sin descripción*"}

---

<small>ID: ${task.gid} | Sincronizado: ${new Date().toLocaleString()}</small>
`.trim();

  const { note: taskNote } = api.createTextNote(parentNoteId, title, content);

  // Labels útiles para búsqueda/filtrado
  taskNote.setLabel("asanaTaskGid", String(task.gid)); // single value :contentReference[oaicite:15]{index=15}
  taskNote.setLabel("status", task.completed ? "completed" : "pending");

  // Multi-valued labels: usa addLabel (no setLabel) :contentReference[oaicite:16]{index=16}
  if (task.projects && task.projects.length) {
    for (const p of task.projects) {
      if (p?.name) taskNote.addLabel("project", p.name);
    }
  }

  if (urgency && showUrgency) taskNote.setLabel("urgency", urgency);

  taskNote.save();
  return taskNote;
}

// ============================================
// 7. FUNCIONES AUXILIARES
// ============================================
function calculateUrgency(dueDate) {
  if (!dueDate) return null;

  const today = new Date();
  const due = new Date(dueDate);
  const diffDays = Math.floor((due - today) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return "overdue";
  if (diffDays === 0) return "today";
  if (diffDays <= 2) return "urgent";
  if (diffDays <= 7) return "soon";
  return "later";
}

function getUrgencyIcon(urgency) {
  return ({
    overdue: "🔥",
    today: "⚠️",
    urgent: "⏰",
    soon: "📅",
    later: "📌",
  }[urgency] || "📝");
}

function getUrgencyBadge(urgency) {
  return ({
    overdue: "**[🔥 VENCIDA]**",
    today: "**[⚠️ HOY]**",
    urgent: "**[⏰ URGENTE]**",
    soon: "**[📅 PRÓXIMO]**",
    later: "",
  }[urgency] || "");
}

// ============================================
// 8. VISTAS ADICIONALES (OPCIONAL)
// ============================================
async function createProjectIndex(tasks, parentNoteId) {
  const projects = {};

  for (const task of tasks) {
    const ps = (task.projects && task.projects.length) ? task.projects : [{ name: "Sin proyecto" }];
    for (const p of ps) {
      const name = p?.name || "Sin proyecto";
      if (!projects[name]) projects[name] = { pending: [], completed: [] };
      (task.completed ? projects[name].completed : projects[name].pending).push(task);
    }
  }

  const { note: indexNote } = api.createTextNote(parentNoteId, "📁 Índice por Proyecto", "");

  for (const [projectName, group] of Object.entries(projects)) {
    const block = `
# ${projectName}

## Tareas Pendientes (${group.pending.length})
${group.pending.map(t => `- ${t.name || "(sin título)"} (${t.permalink_url || ""})`).join("\n") || "*No hay tareas pendientes*"}

## Tareas Completadas (${group.completed.length})
${group.completed.map(t => `- ${t.name || "(sin título)"} (${t.permalink_url || ""})`).join("\n") || "*No hay tareas completadas*"}
`.trim();

    api.createTextNote(indexNote.noteId, `📂 ${projectName}`, block);
  }

  indexNote.save();
}

async function createKanbanView(tasks, parentNoteId) {
  const pending = tasks.filter((t) => !t.completed);

  const byBucket = (bucket) =>
    pending
      .filter((t) => {
        const u = calculateUrgency(t.due_on || t.due_at);
        if (bucket === "later") return !t.due_on && !t.due_at || u === "later";
        if (bucket === "soon") return u === "soon";
        if (bucket === "hot") return ["urgent", "today", "overdue"].includes(u);
        return false;
      })
      .map((t) => `- ${t.name || "(sin título)"} (${t.permalink_url || ""})`)
      .join("\n") || "*Vacío*";

  const content = `
# 📋 Vista Kanban

## 🟡 Por Hacer
${byBucket("later")}

## 🟠 Esta Semana
${byBucket("soon")}

## 🔴 Urgente / Hoy / Vencidas
${byBucket("hot")}

## ✅ Completadas (muestra todas en su sección)
Ve a: "✅ Tareas Completadas"
`.trim();

  api.createTextNote(parentNoteId, "📋 Vista Kanban", content);
}

// ============================================
// 9. (OPCIONAL) CREAR BOTÓN EN LA LAUNCH BAR
// ============================================
// En vez de HTML+onclick (frontend), esta opción crea un “launcher” para correr el script.
// Api.createOrUpdateLauncher existe en backend. :contentReference[oaicite:17]{index=17}
function setupLauncher() {
  const scriptNoteId = api.currentNote.noteId;
  const targetNoteId = getParentNoteId(api.currentNote);

  api.createOrUpdateLauncher({
    id: "asana-sync-all",
    title: "Asana: Sync",
    icon: "bx bx-refresh",
    type: "script",
    isVisible: true,
    keyboardShortcut: "",
    scriptNoteId,
    targetNoteId,
  });

  api.log("✅ Launcher creado/actualizado: Asana: Sync");
}



// ============================================
// EJECUCIÓN
// ============================================

// 1) Descomenta para crear el botón en launchbar:
 // setupLauncher();

// 2) Descomenta para sincronizar ahora:
// await syncAllAsanaTasks();

// Por defecto: no corre solo (para evitar sorpresas).
(async () => {
  await syncAllAsanaTasks();
})().catch(e => api.log(`❌ ${e.stack || e}`));