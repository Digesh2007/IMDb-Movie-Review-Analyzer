const state = {
  rawRows: [],
  rawHeaders: [],
  cleanedRows: null,
  cleanedHeaders: [],
  filename: "",
};

const byId = (id) => document.getElementById(id);
const toast = byId("toast");
let toastTimer;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 3600);
}

function navigate(viewName) {
  const validViews = ["overview", "dataset", "cleaning", "report"];
  const view = validViews.includes(viewName) ? viewName : "overview";
  document.querySelectorAll(".view").forEach((element) => {
    element.classList.toggle("is-visible", element.id === `view-${view}`);
  });
  document.querySelectorAll(".nav-link").forEach((link) => {
    const active = link.dataset.view === view;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  byId("breadcrumb-current").textContent = view.toUpperCase();
  if (window.location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
}

document.querySelectorAll("[data-view]").forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    navigate(link.dataset.view);
  });
});
window.addEventListener("hashchange", () => navigate(window.location.hash.slice(1)));

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (inQuotes) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        inQuotes = false;
      } else {
        field += character;
      }
    } else if (character === '"' && field.length === 0) {
      inQuotes = true;
    } else if (character === ",") {
      row.push(field);
      field = "";
    } else if (character === "\n" || character === "\r") {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      row.push(field);
      if (row.some((value) => value.trim() !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }
  row.push(field);
  if (row.some((value) => value.trim() !== "")) rows.push(row);

  if (inQuotes) throw new Error("The CSV has an unfinished quoted field.");
  if (rows.length === 0) throw new Error("This CSV does not contain a header or records.");

  const headers = rows[0].map((header) => header.replace(/^\uFEFF/, "").trim());
  if (headers.some((header) => !header)) throw new Error("Every column must have a name.");
  if (new Set(headers.map((header) => header.toLowerCase())).size !== headers.length) {
    throw new Error("Column names must be unique (ignoring upper/lowercase). ");
  }

  const records = rows.slice(1).map((values, rowIndex) => {
    const record = {};
    headers.forEach((header, columnIndex) => {
      record[header] = values[columnIndex] ?? "";
    });
    if (values.length > headers.length && values.slice(headers.length).some((value) => value.trim())) {
      throw new Error(`Row ${rowIndex + 2} has more values than the header.`);
    }
    return record;
  });
  return { headers, records };
}

function fieldName(headers, wanted) {
  const target = wanted.toLowerCase();
  return headers.find((header) => header.toLowerCase() === target);
}

function displayValue(value, maxLength = 120) {
  const text = value == null ? "" : String(value).trim();
  if (!text) return "—";
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
}

function renderTable(headers, rows, targetHead, targetBody, emptyTitle, emptyText) {
  const head = byId(targetHead);
  const body = byId(targetBody);
  head.replaceChildren();
  body.replaceChildren();
  const visibleHeaders = headers.slice(0, 7);
  const headerRow = document.createElement("tr");
  visibleHeaders.forEach((header) => {
    const cell = document.createElement("th");
    cell.textContent = header.replaceAll("_", " ").toUpperCase();
    headerRow.append(cell);
  });
  if (headers.length > visibleHeaders.length) {
    const moreHeader = document.createElement("th");
    moreHeader.textContent = "MORE";
    headerRow.append(moreHeader);
  }
  head.append(headerRow);

  if (rows.length === 0) {
    const emptyRow = document.createElement("tr");
    emptyRow.className = "empty-row";
    const cell = document.createElement("td");
    cell.colSpan = Math.max(1, visibleHeaders.length + (headers.length > 7 ? 1 : 0));
    const mark = document.createElement("div");
    mark.className = "empty-mark";
    mark.textContent = "▤";
    const title = document.createElement("strong");
    title.textContent = emptyTitle;
    const text = document.createElement("span");
    text.textContent = emptyText;
    cell.append(mark, title, text);
    emptyRow.append(cell);
    body.append(emptyRow);
    return;
  }

  rows.slice(0, 8).forEach((record) => {
    const row = document.createElement("tr");
    visibleHeaders.forEach((header) => {
      const cell = document.createElement("td");
      cell.textContent = displayValue(record[header]);
      cell.title = record[header] ?? "";
      row.append(cell);
    });
    if (headers.length > 7) {
      const more = document.createElement("td");
      more.textContent = `+${headers.length - 7} fields`;
      more.className = "more-fields";
      row.append(more);
    }
    body.append(row);
  });
}

function renderOverviewRows() {
  const body = byId("review-table-body");
  body.replaceChildren();
  const textField = fieldName(state.rawHeaders, "review_text");
  const movieField = fieldName(state.rawHeaders, "movie_name");
  const titleField = fieldName(state.rawHeaders, "review_title");
  const ratingField = fieldName(state.rawHeaders, "review_rating");
  const dateField = fieldName(state.rawHeaders, "review_date");
  if (!state.rawRows.length || !textField) {
    const row = document.createElement("tr");
    row.className = "empty-row";
    const cell = document.createElement("td");
    cell.colSpan = 4;
    const mark = document.createElement("div");
    mark.className = "empty-mark";
    mark.textContent = "▤";
    const title = document.createElement("strong");
    title.textContent = "No records loaded";
    const text = document.createElement("span");
    text.textContent = "Load a CSV with a review_text column to see a preview.";
    cell.append(mark, title, text);
    row.append(cell);
    body.append(row);
    return;
  }
  state.rawRows.slice(0, 5).forEach((record) => {
    const row = document.createElement("tr");
    [movieField, titleField, ratingField, dateField].forEach((key) => {
      const cell = document.createElement("td");
      cell.textContent = key ? displayValue(record[key], 52) : "—";
      if (key) cell.title = record[key] ?? "";
      row.append(cell);
    });
    body.append(row);
  });
}

function updateDatasetView() {
  const headers = state.cleanedRows ? state.cleanedHeaders : state.rawHeaders;
  const rows = state.cleanedRows ?? state.rawRows;
  renderTable(headers, rows, "dataset-head", "dataset-body", "Your dataset will appear here", "CSV columns are read as provided. No sample reviews are added.");
  const movieKey = fieldName(state.rawHeaders, "movie_name");
  const uniqueMovies = movieKey ? new Set(state.rawRows.map((record) => record[movieKey].trim()).filter(Boolean)).size : 0;
  byId("movie-count").textContent = movieKey ? String(uniqueMovies) : "—";
  byId("movie-count").nextElementSibling.textContent = movieKey ? "Unique titles in imported records" : "Unavailable until movie_name is present";
  byId("raw-count").textContent = String(state.rawRows.length);
  byId("clean-count").textContent = state.cleanedRows ? String(state.cleanedRows.length) : "—";
  byId("duplicate-count").textContent = state.duplicateCount == null ? "—" : String(state.duplicateCount);
  byId("dataset-summary").textContent = `${state.rawRows.length.toLocaleString()} raw record${state.rawRows.length === 1 ? "" : "s"}${state.cleanedRows ? ` · ${state.cleanedRows.length.toLocaleString()} cleaned` : ""}`;
  byId("dataset-filename").textContent = state.filename;
  byId("download-raw").disabled = state.rawRows.length === 0;
  byId("clean-data").disabled = state.rawRows.length === 0;
  byId("clean-data-secondary").disabled = state.rawRows.length === 0;
  byId("download-cleaned").disabled = !state.cleanedRows;
  renderOverviewRows();
}

function stripHtml(text) {
  return String(text).replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function cleanLoadedRecords() {
  if (state.rawRows.length === 0) return;
  const textField = fieldName(state.rawHeaders, "review_text");
  if (!textField) {
    showToast("This CSV has no review_text column, so review cleaning cannot run.");
    return;
  }

  const seenExact = new Set();
  const exactUnique = [];
  state.rawRows.forEach((record) => {
    const signature = JSON.stringify(state.rawHeaders.map((header) => record[header] ?? ""));
    if (!seenExact.has(signature)) {
      seenExact.add(signature);
      exactUnique.push({ ...record });
    }
  });
  const exactRemoved = state.rawRows.length - exactUnique.length;

  const cleanedText = exactUnique.map((record) => {
    const cleanedRecord = { ...record };
    state.rawHeaders.forEach((header) => {
      if (["movie_name", "reviewer_username", "review_title", "review_text", "movie_url", "review_url"].includes(header.toLowerCase())) {
        cleanedRecord[header] = stripHtml(cleanedRecord[header] ?? "");
      }
    });
    return cleanedRecord;
  });

  const withoutEmptyText = cleanedText.filter((record) => String(record[textField] ?? "").trim() !== "");
  const missingTextCount = cleanedText.length - withoutEmptyText.length;
  const movieField = fieldName(state.rawHeaders, "movie_name");
  const titleField = fieldName(state.rawHeaders, "review_title");
  const reviewSignatures = new Set();
  const deduplicated = [];
  withoutEmptyText.forEach((record) => {
    const parts = [movieField, titleField, textField].map((key) => (key ? String(record[key] ?? "").toLowerCase().trim() : ""));
    const signature = JSON.stringify(parts);
    if (!reviewSignatures.has(signature)) {
      reviewSignatures.add(signature);
      deduplicated.push(record);
    }
  });
  const reviewDuplicatesRemoved = withoutEmptyText.length - deduplicated.length;
  let invalidRatings = 0;
  let invalidYears = 0;

  ["movie_rating", "review_rating"].forEach((name) => {
    const key = fieldName(state.rawHeaders, name);
    if (!key) return;
    deduplicated.forEach((record) => {
      const value = String(record[key] ?? "").trim();
      if (!value) {
        record[key] = "";
        return;
      }
      const number = Number(value);
      if (!Number.isFinite(number) || number < 0 || number > 10) {
        invalidRatings += 1;
        record[key] = "";
      } else {
        record[key] = String(number);
      }
    });
  });

  const yearKey = fieldName(state.rawHeaders, "movie_year");
  if (yearKey) {
    deduplicated.forEach((record) => {
      const value = String(record[yearKey] ?? "").trim();
      if (!value) {
        record[yearKey] = "";
        return;
      }
      const year = Number(value);
      if (Number.isInteger(year) && year >= 1800 && year <= 2200) record[yearKey] = String(year);
      else {
        invalidYears += 1;
        record[yearKey] = "";
      }
    });
  }

  ["review_date", "scraped_at"].forEach((name) => {
    const key = fieldName(state.rawHeaders, name);
    if (!key) return;
    deduplicated.forEach((record) => {
      const value = String(record[key] ?? "").trim();
      if (!value) return;
      const date = new Date(value);
      if (!Number.isNaN(date.getTime())) record[key] = date.toISOString().slice(0, 10);
    });
  });

  state.cleanedRows = deduplicated;
  state.cleanedHeaders = [...state.rawHeaders];
  state.duplicateCount = exactRemoved + reviewDuplicatesRemoved;
  state.cleaningSummary = { exactRemoved, reviewDuplicatesRemoved, missingTextCount, invalidRatings, invalidYears };
  byId("cleaning-status-title").textContent = `${deduplicated.length.toLocaleString()} cleaned review${deduplicated.length === 1 ? "" : "s"} ready`;
  byId("cleaning-status-copy").textContent = `${exactRemoved + reviewDuplicatesRemoved} duplicate record(s) removed; ${missingTextCount} row(s) with missing review text removed.`;
  setCleaningResult("exact-duplicates", `${exactRemoved + reviewDuplicatesRemoved} REMOVED`, "done");
  setCleaningResult("text-cleaned", "NORMALIZED", "done");
  setCleaningResult("missing-text", `${missingTextCount} REMOVED`, missingTextCount ? "warning" : "done");
  const invalidSummary = `${invalidRatings} INVALID RATING${invalidRatings === 1 ? "" : "S"}${invalidYears ? ` · ${invalidYears} YEAR` : ""}`;
  setCleaningResult("invalid-ratings", invalidRatings || invalidYears ? invalidSummary : "VALIDATED", invalidRatings || invalidYears ? "warning" : "done");
  byId("export-note").textContent = `${deduplicated.length.toLocaleString()} cleaned records · values outside validation ranges are blanked in the cleaned copy.`;
  updateDatasetView();
  showToast(`Cleaning complete. ${deduplicated.length} real review rows are ready for export.`);
}

function setCleaningResult(id, text, status) {
  const element = byId(id);
  element.textContent = text;
  element.classList.toggle("is-done", status === "done");
  element.classList.toggle("is-warning", status === "warning");
}

function csvEscape(value) {
  const text = value == null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function downloadCsv(headers, rows, filename) {
  if (!headers.length || !rows.length) return;
  const lines = [headers.map(csvEscape).join(",")];
  rows.forEach((record) => lines.push(headers.map((header) => csvEscape(record[header])).join(",")));
  const blob = new Blob(["\uFEFF", lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

byId("csv-file").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const parsed = parseCsv(await file.text());
    state.rawHeaders = parsed.headers;
    state.rawRows = parsed.records;
    state.cleanedRows = null;
    state.cleanedHeaders = [];
    state.filename = file.name;
    state.duplicateCount = null;
    state.cleaningSummary = null;
    byId("cleaning-status-title").textContent = "Waiting for cleaning";
    byId("cleaning-status-copy").textContent = "Review the imported columns, then run the cleaning pass when ready.";
    byId("export-note").textContent = "The cleaned CSV is available after processing a loaded dataset.";
    ["exact-duplicates", "text-cleaned", "missing-text", "invalid-ratings"].forEach((id) => setCleaningResult(id, "WAITING", ""));
    updateDatasetView();
    navigate("dataset");
    showToast(`Loaded ${parsed.records.length} record(s) from ${file.name}.`);
  } catch (error) {
    showToast(error instanceof Error ? error.message : "Could not read this CSV file.");
  } finally {
    event.target.value = "";
  }
});

byId("clean-data").addEventListener("click", cleanLoadedRecords);
byId("clean-data-secondary").addEventListener("click", cleanLoadedRecords);
byId("download-raw").addEventListener("click", () => downloadCsv(state.rawHeaders, state.rawRows, "raw_imdb_reviews.csv"));
byId("download-cleaned").addEventListener("click", () => downloadCsv(state.cleanedHeaders, state.cleanedRows ?? [], "cleaned_imdb_reviews.csv"));

navigate(window.location.hash.slice(1));
