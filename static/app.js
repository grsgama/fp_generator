const state = {
  meta: { categories: {} },
  equipment: [],
  recipes: [],
  sheets: [],
  generated: [],
  audit: [],
  recipeRevisions: [],
  sheetRevisions: [],
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Erro de API");
  }
  return response.json();
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(node.timer);
  node.timer = setTimeout(() => node.classList.remove("show"), 3200);
}

function fillCategorySelect(select, selected = "") {
  select.innerHTML = "";
  Object.keys(state.meta.categories).forEach((category) => {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    select.append(option);
  });
  if (selected) select.value = selected;
  fillSubtypeSelect(select.closest("form"), select.value);
}

function fillSubtypeSelect(form, category, selected = "") {
  const select = $("select[name='subtype']", form);
  if (!select) return;
  select.innerHTML = "";
  (state.meta.categories[category] || []).forEach((subtype) => {
    const option = document.createElement("option");
    option.value = subtype;
    option.textContent = subtype;
    select.append(option);
  });
  if (selected) select.value = selected;
}

function fillEquipmentSelect(select, selected = "") {
  select.innerHTML = "";
  state.equipment.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = `${item.name} - ${item.category} / ${item.subtype}`;
    select.append(option);
  });
  if (selected) select.value = String(selected);
}

function fillRecipeSelect(select, selected = "") {
  select.innerHTML = "";
  state.recipes.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = `${item.name} - ${item.category} / ${item.subtype}`;
    select.append(option);
  });
  if (selected) select.value = String(selected);
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function resetForm(formId) {
  const form = $(`#${formId}`);
  form.reset();
  $("input[name='id']", form).value = "";
  if (formId === "recipeForm") {
    $("#recipeParams").innerHTML = "";
    addRecipeParamRow();
  }
  if (formId === "sheetForm") {
    $("#sheetBlocks").innerHTML = "";
    addSheetBlockRow();
    updateSheetBlockOrder();
  }
}

function renderEquipment() {
  const list = $("#equipmentList");
  list.innerHTML = "";
  if (!state.equipment.length) {
    list.innerHTML = "<p class='muted'>Nenhum equipamento cadastrado.</p>";
    return;
  }
  state.equipment.forEach((item) => {
    const node = document.createElement("article");
    node.className = "item";
    node.innerHTML = `
      <div class="item-header">
        <div>
          <div class="item-title">${item.name}</div>
          <div class="muted">${item.model || "-"} ${item.manufacturer ? `| ${item.manufacturer}` : ""}</div>
          <div class="tags">
            <span class="tag">${item.category}</span>
            <span class="tag">${item.subtype}</span>
            <span class="tag">${item.status}</span>
            ${item.location ? `<span class="tag">${item.location}</span>` : ""}
          </div>
        </div>
        <div class="item-actions">
          <button class="secondary" data-edit-equipment="${item.id}">Editar</button>
          <button class="danger" data-delete-equipment="${item.id}">Remover</button>
        </div>
      </div>
      ${item.notes ? `<p>${item.notes}</p>` : ""}
    `;
    list.append(node);
  });
}

function renderRecipes() {
  const select = $("#recipeForm select[name='equipment_id']");
  fillEquipmentSelect(select);
  const list = $("#recipeList");
  list.innerHTML = "";
  if (!state.recipes.length) {
    list.innerHTML = "<p class='muted'>Nenhum bloco cadastrado.</p>";
    return;
  }
  state.recipes.forEach((item) => {
    const params = item.parameters.map((p) => `${p.name}: ${p.value || "-"}${p.unit ? ` ${p.unit}` : ""}`).join("<br>");
    const node = document.createElement("article");
    node.className = "item";
    node.innerHTML = `
      <div class="item-header">
        <div>
          <div class="item-title">${item.name}</div>
          <div class="muted">${item.equipment_name} ${item.equipment_model ? `| ${item.equipment_model}` : ""}</div>
          <div class="tags">
            <span class="tag">${item.category}</span>
            <span class="tag">${item.subtype}</span>
            <span class="tag">${item.confidence_level}</span>
            ${item.author ? `<span class="tag">${item.author}</span>` : ""}
          </div>
        </div>
        <div class="item-actions">
          <button class="secondary" data-edit-recipe="${item.id}">Editar</button>
          <button class="secondary" data-duplicate-recipe="${item.id}">Duplicar</button>
          <button class="danger" data-delete-recipe="${item.id}">Remover</button>
        </div>
      </div>
      ${item.description ? `<p>${item.description}</p>` : ""}
      ${params ? `<p class="muted">${params}</p>` : ""}
    `;
    list.append(node);
  });
}

function renderSheets() {
  const list = $("#sheetList");
  list.innerHTML = "";
  if (!state.sheets.length) {
    list.innerHTML = "<p class='muted'>Nenhuma folha cadastrada.</p>";
    return;
  }
  state.sheets.forEach((item) => {
    const blocks = item.blocks.map((b) => `${b.seq}. ${b.title_override || b.recipe_name}`).join("<br>");
    const node = document.createElement("article");
    node.className = "item";
    node.innerHTML = `
      <div class="item-header">
        <div>
          <div class="item-title">${item.title}</div>
          <div class="muted">${item.project_name || "-"} ${item.author ? `| ${item.author}` : ""}</div>
          <div class="tags">
            <span class="tag">${item.status}</span>
            <span class="tag">${item.blocks.length} bloco(s)</span>
          </div>
        </div>
        <div class="item-actions">
          <button class="secondary" data-edit-sheet="${item.id}">Editar</button>
          <button data-generate-sheet="${item.id}">Gerar XLSX</button>
          <button class="danger" data-delete-sheet="${item.id}">Remover</button>
        </div>
      </div>
      ${item.description ? `<p>${item.description}</p>` : ""}
      ${blocks ? `<p class="muted">${blocks}</p>` : ""}
    `;
    list.append(node);
  });
}

function renderHistory() {
  const list = $("#historyList");
  list.innerHTML = "";
  if (!state.generated.length) {
    list.innerHTML = "<p class='muted'>Nenhum arquivo gerado.</p>";
    return;
  }
  state.generated.forEach((item) => {
    const node = document.createElement("article");
    node.className = "item";
    node.innerHTML = `
      <div class="item-header">
        <div>
          <div class="item-title">${item.process_sheet_title || "Folha removida"}</div>
          <div class="muted">${item.created_at}</div>
          <div class="muted">${item.output_path}</div>
        </div>
        <a href="/download/${item.id}"><button>Baixar</button></a>
      </div>
    `;
    list.append(node);
  });
}

function renderAudit() {
  const list = $("#auditList");
  list.innerHTML = "";
  if (!state.audit.length) {
    list.innerHTML = "<p class='muted'>Nenhum evento de auditoria.</p>";
    return;
  }
  state.audit.forEach((item) => {
    const node = document.createElement("article");
    node.className = "item";
    node.innerHTML = `
      <div class="item-header">
        <div>
          <div class="item-title">${item.entity_type} #${item.entity_id ?? "-"}</div>
          <div class="muted">${item.action} | ${item.created_at}</div>
          <div class="muted">${item.payload || "-"}</div>
        </div>
      </div>
    `;
    list.append(node);
  });
}

function renderRevisions() {
  const recipeList = $("#recipeRevisionList");
  const sheetList = $("#sheetRevisionList");
  recipeList.innerHTML = "";
  sheetList.innerHTML = "";

  const recipeRows = state.recipeRevisions.slice(0, 10);
  const sheetRows = state.sheetRevisions.slice(0, 10);

  if (!recipeRows.length) {
    recipeList.innerHTML = "<p class='muted'>Sem revisoes de blocos.</p>";
  } else {
    recipeRows.forEach((item) => {
      const node = document.createElement("article");
      node.className = "item";
      node.innerHTML = `
        <div class="item-header">
          <div>
            <div class="item-title">Bloco #${item.recipe_block_id} v${item.revision_no}</div>
            <div class="muted">${item.action} | ${item.created_at}</div>
            <div class="muted">${item.payload}</div>
          </div>
        </div>
      `;
      recipeList.append(node);
    });
  }

  if (!sheetRows.length) {
    sheetList.innerHTML = "<p class='muted'>Sem revisoes de folhas.</p>";
  } else {
    sheetRows.forEach((item) => {
      const node = document.createElement("article");
      node.className = "item";
      node.innerHTML = `
        <div class="item-header">
          <div>
            <div class="item-title">Folha #${item.process_sheet_id} v${item.revision_no}</div>
            <div class="muted">${item.action} | ${item.created_at}</div>
            <div class="muted">${item.payload}</div>
          </div>
        </div>
      `;
      sheetList.append(node);
    });
  }
}

async function loadLatestRevisions() {
  state.recipeRevisions = [];
  state.sheetRevisions = [];
  if (state.recipes.length) {
    state.recipeRevisions = await api(`/api/recipe-blocks/${state.recipes[0].id}/revisions`).catch(() => []);
  }
  if (state.sheets.length) {
    state.sheetRevisions = await api(`/api/process-sheets/${state.sheets[0].id}/revisions`).catch(() => []);
  }
}

function addRecipeParamRow(param = {}) {
  const row = document.createElement("div");
  row.className = "param-row";
  row.innerHTML = `
    <input data-param="name" placeholder="Parametro" value="${param.name || ""}" />
    <input data-param="value" placeholder="Valor" value="${param.value || ""}" />
    <input data-param="unit" placeholder="Unidade" value="${param.unit || ""}" />
    <button type="button" class="danger icon-button" data-remove-row>×</button>
  `;
  $("#recipeParams").append(row);
}

function addSheetBlockRow(block = {}) {
  const row = document.createElement("div");
  row.className = "sheet-block-row";
  row.draggable = true;
  row.innerHTML = `
    <span class="drag-handle" title="Arrastar para reordenar">↕</span>
    <input data-sheet-block="seq" type="number" min="1" placeholder="Ordem" value="${block.seq || ""}" readonly />
    <select data-sheet-block="recipe_block_id"></select>
    <input data-sheet-block="title_override" placeholder="Titulo opcional" value="${block.title_override || ""}" />
    <input data-sheet-block="notes_override" placeholder="Nota opcional" value="${block.notes_override || ""}" />
    <button type="button" class="danger icon-button" data-remove-row>×</button>
  `;
  fillRecipeSelect($("select", row), block.recipe_block_id || "");
  bindSheetBlockDrag(row);
  $("#sheetBlocks").append(row);
  updateSheetBlockOrder();
}

function updateSheetBlockOrder() {
  $$("#sheetBlocks .sheet-block-row").forEach((row, index) => {
    $("[data-sheet-block='seq']", row).value = index + 1;
  });
}

function bindSheetBlockDrag(row) {
  row.addEventListener("dragstart", () => {
    row.classList.add("dragging");
  });
  row.addEventListener("dragend", () => {
    row.classList.remove("dragging");
    updateSheetBlockOrder();
  });
}

function getDragAfterElement(container, y) {
  const rows = [...container.querySelectorAll(".sheet-block-row:not(.dragging)")];
  return rows.reduce(
    (closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset, element: child };
      }
      return closest;
    },
    { offset: Number.NEGATIVE_INFINITY, element: null }
  ).element;
}

function recipeParamsPayload() {
  return $$("#recipeParams .param-row")
    .map((row) => ({
      name: $("[data-param='name']", row).value.trim(),
      value: $("[data-param='value']", row).value.trim(),
      unit: $("[data-param='unit']", row).value.trim(),
    }))
    .filter((param) => param.name);
}

function sheetBlocksPayload() {
  return $$("#sheetBlocks .sheet-block-row")
    .map((row, index) => ({
      recipe_block_id: Number($("[data-sheet-block='recipe_block_id']", row).value),
      seq: Number($("[data-sheet-block='seq']", row).value || index + 1),
      title_override: $("[data-sheet-block='title_override']", row).value.trim(),
      notes_override: $("[data-sheet-block='notes_override']", row).value.trim(),
    }))
    .filter((block) => block.recipe_block_id);
}

async function loadAll() {
  state.meta = await api("/api/meta");
  const status = $("#templateStatus");
  status.textContent = state.meta.template_exists ? "Template XLSX encontrado" : "Template XLSX ausente";
  status.className = `status-pill ${state.meta.template_exists ? "ok" : "warn"}`;

  $$("select[name='category']").forEach((select) => fillCategorySelect(select));
  state.equipment = await api("/api/equipment?include_inactive=true");
  state.recipes = await api("/api/recipe-blocks");
  state.sheets = await api("/api/process-sheets");
  state.generated = await api("/api/generated");
  state.audit = await api("/api/audit?limit=50");
  await loadLatestRevisions();
  $$("#sheetBlocks select").forEach((select) => fillRecipeSelect(select));
  renderEquipment();
  renderRecipes();
  renderSheets();
  renderHistory();
  renderAudit();
  renderRevisions();
}

async function refreshData() {
  state.equipment = await api("/api/equipment?include_inactive=true");
  state.recipes = await api("/api/recipe-blocks");
  state.sheets = await api("/api/process-sheets");
  state.generated = await api("/api/generated");
  state.audit = await api("/api/audit?limit=50");
  await loadLatestRevisions();
  $$("#sheetBlocks select").forEach((select) => fillRecipeSelect(select, select.value));
  renderEquipment();
  renderRecipes();
  renderSheets();
  renderHistory();
  renderAudit();
  renderRevisions();
}

function bindEvents() {
  $$(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      $$(".tab").forEach((item) => item.classList.remove("active"));
      $$(".view").forEach((view) => view.classList.remove("active"));
      tab.classList.add("active");
      $(`#${tab.dataset.view}`).classList.add("active");
    });
  });

  $$("select[name='category']").forEach((select) => {
    select.addEventListener("change", () => fillSubtypeSelect(select.closest("form"), select.value));
  });

  $$("[data-reset]").forEach((button) => {
    button.addEventListener("click", () => resetForm(button.dataset.reset));
  });

  $("#addRecipeParam").addEventListener("click", () => addRecipeParamRow());
  $("#addSheetBlock").addEventListener("click", () => addSheetBlockRow());

  document.addEventListener("click", async (event) => {
    const target = event.target;
    if (target.matches("[data-remove-row]")) {
      target.closest(".param-row, .sheet-block-row").remove();
      updateSheetBlockOrder();
    }
    if (target.matches("[data-edit-equipment]")) editEquipment(Number(target.dataset.editEquipment));
    if (target.matches("[data-edit-recipe]")) editRecipe(Number(target.dataset.editRecipe));
    if (target.matches("[data-edit-sheet]")) editSheet(Number(target.dataset.editSheet));
    if (target.matches("[data-duplicate-recipe]")) await duplicateRecipe(Number(target.dataset.duplicateRecipe));
    if (target.matches("[data-delete-equipment]")) await removeItem(`/api/equipment/${target.dataset.deleteEquipment}`);
    if (target.matches("[data-delete-recipe]")) await removeItem(`/api/recipe-blocks/${target.dataset.deleteRecipe}`);
    if (target.matches("[data-delete-sheet]")) await removeItem(`/api/process-sheets/${target.dataset.deleteSheet}`);
    if (target.matches("[data-generate-sheet]")) await generateSheet(Number(target.dataset.generateSheet));
  });

  $("#equipmentForm").addEventListener("submit", saveEquipment);
  $("#recipeForm").addEventListener("submit", saveRecipe);
  $("#sheetForm").addEventListener("submit", saveSheet);
  $("#sheetBlocks").addEventListener("dragover", (event) => {
    event.preventDefault();
    const dragging = $(".sheet-block-row.dragging");
    if (!dragging) return;
    const afterElement = getDragAfterElement($("#sheetBlocks"), event.clientY);
    if (afterElement == null) {
      $("#sheetBlocks").appendChild(dragging);
    } else {
      $("#sheetBlocks").insertBefore(dragging, afterElement);
    }
    updateSheetBlockOrder();
  });
}

async function removeItem(path) {
  if (!confirm("Confirmar remocao?")) return;
  try {
    await api(path, { method: "DELETE" });
    await refreshData();
    toast("Registro removido");
  } catch (error) {
    toast(error.message);
  }
}

async function saveEquipment(event) {
  event.preventDefault();
  const data = formData(event.currentTarget);
  const id = data.id;
  delete data.id;
  try {
    await api(id ? `/api/equipment/${id}` : "/api/equipment", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(data),
    });
    resetForm("equipmentForm");
    await refreshData();
    toast("Equipamento salvo");
  } catch (error) {
    toast(error.message);
  }
}

async function saveRecipe(event) {
  event.preventDefault();
  const data = formData(event.currentTarget);
  const id = data.id;
  delete data.id;
  data.equipment_id = Number(data.equipment_id);
  data.parameters = recipeParamsPayload();
  try {
    await api(id ? `/api/recipe-blocks/${id}` : "/api/recipe-blocks", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(data),
    });
    resetForm("recipeForm");
    await refreshData();
    toast("Bloco salvo");
  } catch (error) {
    toast(error.message);
  }
}

async function duplicateRecipe(id) {
  try {
    await api(`/api/recipe-blocks/${id}/duplicate`, { method: "POST" });
    await refreshData();
    toast("Bloco duplicado");
  } catch (error) {
    toast(error.message);
  }
}

async function saveSheet(event) {
  event.preventDefault();
  const data = formData(event.currentTarget);
  const id = data.id;
  delete data.id;
  data.blocks = sheetBlocksPayload();
  try {
    await api(id ? `/api/process-sheets/${id}` : "/api/process-sheets", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(data),
    });
    resetForm("sheetForm");
    await refreshData();
    toast("Folha salva");
  } catch (error) {
    toast(error.message);
  }
}

function editEquipment(id) {
  const item = state.equipment.find((entry) => entry.id === id);
  const form = $("#equipmentForm");
  Object.entries(item).forEach(([key, value]) => {
    const input = $(`[name='${key}']`, form);
    if (input) input.value = value || "";
  });
  fillSubtypeSelect(form, item.category, item.subtype);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function editRecipe(id) {
  const item = state.recipes.find((entry) => entry.id === id);
  const form = $("#recipeForm");
  Object.entries(item).forEach(([key, value]) => {
    const input = $(`[name='${key}']`, form);
    if (input) input.value = value || "";
  });
  fillSubtypeSelect(form, item.category, item.subtype);
  fillEquipmentSelect($("select[name='equipment_id']", form), item.equipment_id);
  $("#recipeParams").innerHTML = "";
  item.parameters.forEach((param) => addRecipeParamRow(param));
  if (!item.parameters.length) addRecipeParamRow();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function editSheet(id) {
  const item = state.sheets.find((entry) => entry.id === id);
  const form = $("#sheetForm");
  Object.entries(item).forEach(([key, value]) => {
    const input = $(`[name='${key}']`, form);
    if (input) input.value = value || "";
  });
  $("#sheetBlocks").innerHTML = "";
  item.blocks.forEach((block) => addSheetBlockRow(block));
  if (!item.blocks.length) addSheetBlockRow();
  updateSheetBlockOrder();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function generateSheet(id) {
  try {
    const generated = await api(`/api/process-sheets/${id}/generate`, { method: "POST" });
    await refreshData();
    toast("XLSX gerado");
    window.location.href = `/download/${generated.id}`;
  } catch (error) {
    toast(error.message);
  }
}

bindEvents();
addRecipeParamRow();
addSheetBlockRow();
updateSheetBlockOrder();
loadAll().catch((error) => toast(error.message));
