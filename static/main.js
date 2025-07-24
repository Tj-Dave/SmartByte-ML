// ==== SIDEBAR TOGGLE (Mobile) ====
document.querySelector(".toggle-sidebar").addEventListener("click", toggleSidebar);

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("active");
}

// ==== DROPDOWN MENU (Desktop) ====
const menuButton = document.querySelector(".menu-button");
const menuContent = document.querySelector(".menu-content");

menuButton.addEventListener("click", (e) => {
  e.stopPropagation();
  menuContent.style.display = menuContent.style.display === "block" ? "none" : "block";
});

// ==== MODALS: About & Theme ====
const aboutLink = document.getElementById("about-link");
const aboutModal = document.getElementById("about-modal");

aboutLink.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  aboutModal.classList.toggle("show");
  menuContent.style.display = "none";
});

const themeLink = document.getElementById("theme-settings");
const themeModal = document.getElementById("theme-modal");

themeLink.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  themeModal.classList.toggle("show");
  menuContent.style.display = "none";
});

// ==== OUTSIDE CLICK HANDLER ====
document.addEventListener("click", (e) => {
  if (!menuButton.contains(e.target) && !menuContent.contains(e.target)) {
    menuContent.style.display = "none";
  }

  if (!aboutModal.contains(e.target)) {
    aboutModal.classList.remove("show");
  }

  if (!themeModal.contains(e.target)) {
    themeModal.classList.remove("show");
  }
});

// ==== THEME HANDLING ====
function applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else if (theme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

function loadSavedTheme() {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme) {
    applyTheme(savedTheme);
    const radio = document.querySelector(`input[name="theme"][value="${savedTheme}"]`);
    if (radio) radio.checked = true;
  }
}
loadSavedTheme();

document.querySelectorAll('input[name="theme"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    const selected = radio.value;
    localStorage.setItem("theme", selected);
    applyTheme(selected);
    updateMapStyle(selected);
  });
});

// ==== MAPBOX INITIALIZATION ====
mapboxgl.accessToken = 'pk.eyJ1IjoiY3JlYXRpdmVkb21haW4iLCJhIjoiY21kZ2l4Z2VuMG1jbzJ3c2d6cmx1eWExOCJ9.JUbKmPV39rda7ggoUEmMiA';

let map = null;
function initMap() {
  const theme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = theme === "dark" || (!theme && prefersDark);

  map = new mapboxgl.Map({
    container: 'map',
    style: isDark ? 'mapbox://styles/creativedomain/cmdglljq3000601s8c7nwe9tp' : 'mapbox://styles/creativedomain/cmdhi8yrn002501s81c58dkj8',
    center: [31.1825, -0.2],
    pitch: 65,
    bearing: 25,
    zoom: 7.95
  });
}
initMap();

function updateMapStyle(theme) {
  if (!map) return;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = theme === "dark" || (!theme && prefersDark);
  const newStyle = isDark ? 'mapbox://styles/mapbox/dark-v11' : 'mapbox://styles/mapbox/streets-v11';
  map.setStyle(newStyle);
}

// ==== FORM HANDLING ====
document.getElementById("search-form").addEventListener("submit", function (e) {
  e.preventDefault();

  const city = document.getElementById("city-input").value;
  const dateInput = document.getElementById("date-input").value;
  const [year, month] = dateInput.split("-");
  const date = `${year}-${month}-01`;

  if (parseInt(year) < 2025 || (parseInt(year) === 2025 && parseInt(month) < 7)) {
    alert("Please select a date from July 2025 onwards.");
    return;
  }

  if (parseInt(year) > 2050) {
    alert("Please select a date before January 2051.");
    return;
  }

  fetch(`/flood-map/${city}/${date}`)
    .then((res) => res.json())
    .then((data) => {
      renderMap(city, data);
    })
    .catch((err) => console.error("Error fetching data:", err));
});

const cityCoords = {
  Kampala: [32.5816, 0.3152],
  Kasese: [30.08572, 0.17236],
  Kabale: [29.989889, -1.256889],
};

const cityBearing = {
  Kampala: 20,
  Kasese: -40,
  Kabale: 0,
};

const cityPitch = {
  Kampala: 65,
  Kasese: 80,
  Kabale: 75,
};

function renderMap(city, geojson) {
  if (!map) return;

  const cityCoord = cityCoords[city];
  if (cityCoord) {
    new mapboxgl.Marker({ color: "red" })
      .setLngLat(cityCoord)
      .addTo(map);
    map.flyTo({ center: cityCoord, zoom: 15.5, speed: 0.5, bearing: cityBearing[city] || 0, pitch: cityPitch[city] || 65 });
  }

  geojson.features.forEach((feature) => {
    const coords = getPolygonCenter(feature.geometry.coordinates[0]);
    const props = feature.properties;

    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(
      `<strong>${props.name}</strong><br>
      Probability: ${props.probability}<br>
      Size Covered: ${props.size_covered}<br>
      Population Affected: ${props.population_affected}`
    );

    new mapboxgl.Marker({ color: "blue" })
      .setLngLat(coords)
      .setPopup(popup)
      .addTo(map);
  });
}

function getPolygonCenter(coords) {
  let x = 0,
    y = 0;
  coords.forEach((c) => {
    x += c[0];
    y += c[1];
  });
  return [x / coords.length, y / coords.length];
}