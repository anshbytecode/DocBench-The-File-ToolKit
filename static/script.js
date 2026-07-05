(function () {
  const form = document.getElementById("tool-form");
  if (!form) return;

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const fileListEl = document.getElementById("file-list");
  const statusEl = document.getElementById("status");
  const diffOutput = document.getElementById("diff-output");
  const runBtn = form.querySelector(".run-btn");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      fileInput.files = e.dataTransfer.files;
      updateFileList();
    });
    fileInput.addEventListener("change", updateFileList);
  }

  function updateFileList() {
    const files = fileInput.files;
    if (!files || files.length === 0) {
      fileListEl.textContent = "No file selected";
    } else if (files.length === 1) {
      fileListEl.textContent = files[0].name;
    } else {
      fileListEl.textContent = `${files.length} files selected`;
    }
  }

  function filenameFromDisposition(disposition, fallback) {
    if (!disposition) return fallback;
    const match = /filename="?([^"]+)"?/.exec(disposition);
    return match ? match[1] : fallback;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    statusEl.textContent = "Processing…";
    statusEl.className = "status";
    runBtn.disabled = true;
    diffOutput.innerHTML = "";

    const formData = new FormData();

    if (fileInput) {
      const files = fileInput.files;
      if (files.length === 0) {
        statusEl.textContent = "Please choose a file first.";
        statusEl.className = "status error";
        runBtn.disabled = false;
        return;
      }
      if (MULTIPLE) {
        for (const f of files) formData.append("file", f);
      } else {
        formData.append("file", files[0]);
      }
    }

    // append all non-file form fields
    Array.from(form.elements).forEach((el) => {
      if (el.name && el.type !== "file" && el.type !== "submit") {
        formData.append(el.name, el.value);
      }
    });

    try {
      const res = await fetch(`/process/${TOOL_ID}`, { method: "POST", body: formData });

      if (!res.ok) {
        const ct = res.headers.get("content-type") || "";
        if (ct.includes("application/json")) {
          const errJson = await res.json();
          throw new Error(errJson.error || "Something went wrong.");
        }
        throw new Error(`Request failed (${res.status})`);
      }

      const contentType = res.headers.get("content-type") || "";

      if (RESULT_TYPE === "html" || contentType.includes("text/html")) {
        const html = await res.text();
        diffOutput.innerHTML = html;
        statusEl.textContent = "Done.";
        statusEl.className = "status success";
      } else {
        const blob = await res.blob();
        const disposition = res.headers.get("content-disposition");
        const filename = filenameFromDisposition(disposition, "result");
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        statusEl.textContent = `Done — downloaded ${filename}`;
        statusEl.className = "status success";
      }
    } catch (err) {
      statusEl.textContent = err.message || "Something went wrong.";
      statusEl.className = "status error";
    } finally {
      runBtn.disabled = false;
    }
  });
})();
