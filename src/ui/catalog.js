function setOptions(selectElement, options, selectedValue) {
  selectElement.innerHTML = "";
  options.forEach(({ value, label }) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    option.selected = value === selectedValue;
    selectElement.appendChild(option);
  });
}

export function renderCatalogOptions(dom, catalog, currentValues) {
  setOptions(
    dom.category,
    Object.entries(catalog.categories).map(([value, item]) => ({
      value,
      label: item.label ?? value
    })),
    currentValues.category
  );

  setOptions(
    dom.platform,
    Object.entries(catalog.platforms).map(([value, label]) => ({
      value,
      label
    })),
    currentValues.platform
  );

  setOptions(
    dom.objective,
    Object.entries(catalog.objectives).map(([value, label]) => ({
      value,
      label
    })),
    currentValues.objective
  );

  setOptions(
    dom.tone,
    Object.entries(catalog.tones).map(([value, item]) => ({
      value,
      label: item.label ?? value
    })),
    currentValues.tone
  );
}
