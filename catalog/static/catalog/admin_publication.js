(function () {
  "use strict";

  function addRemoveButton(fieldName, label) {
    const chosen = document.querySelector(`#id_${fieldName}_to`);
    const panel = chosen && chosen.closest(".selector-chosen");
    const removeLink = document.getElementById(`id_${fieldName}_remove_link`);
    if (!chosen || !removeLink || !panel) return;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "button";
    button.textContent = label;
    button.style.marginTop = "8px";
    button.addEventListener("click", function () {
      if (Array.from(chosen.options).some((option) => option.selected)) {
        removeLink.click();
      } else {
        window.alert("请先在已选列表中选中要移除的项目。");
      }
    });
    panel.appendChild(button);
  }

  document.addEventListener("DOMContentLoaded", function () {
    addRemoveButton("members", "移除选中的组内作者");
    addRemoveButton("keywords", "移除选中的关键词");
  });
})();
