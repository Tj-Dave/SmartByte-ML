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
document.addEventListener("click", (e) => {
  if (!menuButton.contains(e.target) && !menuContent.contains(e.target)) {
    menuContent.style.display = "none";
  }
  if (!aboutModal.contains(e.target)) aboutModal.classList.remove("show");
  if (!themeModal.contains(e.target)) themeModal.classList.remove("show");
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
      if (data.error) {
        alert("Error: " + data.error);
        return;
      }
      renderMap(city, data);
    })
    .catch((err) => console.error("Error fetching data:", err));

  // Load analytics data - Fixed syntax error
  if (window.analyticsDashboard) {
    window.analyticsDashboard.loadAnalytics(city, date);
  }
});

const cityCoords = {
  Kampala: [32.5816, 0.3152],
  Kasese: [30.08572, 0.17236],
  Kabale: [29.989889, -1.256889],
};
const cityBearing = { Kampala: 20, Kasese: -40, Kabale: 0 };
const cityPitch = { Kampala: 65, Kasese: 80, Kabale: 75 };

function renderMap(city, geojson) {
  if (!map) return;

  const cityCoord = cityCoords[city];
  if (cityCoord) {
    map.flyTo({
      center: cityCoord,
      zoom: 14,
      speed: 0.7,
      bearing: cityBearing[city] || 0,
      pitch: cityPitch[city] || 65
    });
  }

  // Remove previous layers
  if (map.getSource('flood-geojson')) {
    if (map.getLayer('flood-fill')) map.removeLayer('flood-fill');
    if (map.getLayer('flood-outline')) map.removeLayer('flood-outline');
    map.removeSource('flood-geojson');
  }

  // Add source
  map.addSource('flood-geojson', {
    type: 'geojson',
    data: geojson
  });

  // Fill layer
  map.addLayer({
    id: 'flood-fill',
    type: 'fill',
    source: 'flood-geojson',
    paint: {
      'fill-color': [
        'match',
        ['get', 'risk_level'],
        'low', '#2ECC71',
        'medium', '#F1C40F',
        'high', '#E74C3C',
        '#ccc'
      ],
      'fill-opacity': 0.55
    }
  });

  // Outline layer
  map.addLayer({
    id: 'flood-outline',
    type: 'line',
    source: 'flood-geojson',
    paint: {
      'line-color': '#34495E',
      'line-width': 1.2
    }
  });

  // Add polygon hover effect
  map.on('mousemove', 'flood-fill', (e) => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'flood-fill', () => {
    map.getCanvas().style.cursor = '';
  });

  // Add click popup
  map.on('click', 'flood-fill', (e) => {
    const props = e.features[0].properties;

    new mapboxgl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(
        `<strong>${props.town}</strong><br>
        Risk Level: <b>${props.risk_level}</b><br>
        Probability: ${parseFloat(props.probability).toFixed(2)}<br>
        Size Covered: ${parseFloat(props.size_covered).toFixed(1)} km²<br>
        Population Affected: ${props.population_affected}`
      )
      .addTo(map);
  });

  // Optionally still add center markers (can remove if not needed)
  geojson.features.forEach((feature) => {
    const coords = getPolygonCenter(feature.geometry.coordinates[0]);
    new mapboxgl.Marker({ color: "blue" }).setLngLat(coords).addTo(map);
  });
}

function getPolygonCenter(coords) {
  let x = 0, y = 0;
  coords.forEach((c) => {
    x += c[0];
    y += c[1];
  });
  return [x / coords.length, y / coords.length];
}

// ==== MAP COLOR SCALE & LEGEND ====

function getProbabilityColor(prob) {
  if (prob <= 0.2) return '#0000FF';
  if (prob <= 0.4) return '#00FFFF';
  if (prob <= 0.6) return '#FFFF00';
  if (prob <= 0.8) return '#FFA500';
  return '#FF0000';
}

// Add Mapbox Navigation Controls (top-right)
map.addControl(new mapboxgl.NavigationControl(), 'top-right');

// Add dynamic fill color based on probability instead of static risk_level
map.on('style.load', () => {
  // Re-add flood layer if needed on style change
  if (map.getSource('flood-geojson')) {
    map.addLayer({
      id: 'flood-fill',
      type: 'fill',
      source: 'flood-geojson',
      paint: {
        'fill-color': [
          'interpolate',
          ['linear'],
          ['get', 'probability'],
          0.05, '#0000FF',
          0.2, '#00FFFF',
          0.4, '#FFFF00',
          0.6, '#FFA500',
          0.8, '#FF0000'
        ],
        'fill-opacity': 0.6
      }
    });

    map.addLayer({
      id: 'flood-outline',
      type: 'line',
      source: 'flood-geojson',
      paint: {
        'line-color': '#34495E',
        'line-width': 1.2
      }
    });
  }
});

// ==== Add Legend ====
const legend = document.createElement('div');
legend.id = 'legend';
legend.style.cssText = `
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.47);
  padding: 10px;
  font-size: 12px;
  border-radius: 4px;
  box-shadow: 0 0 5px rgba(0,0,0,0.3);
  z-index: 1;
`;

legend.innerHTML = `
  <h4 style="margin-top:0">Flood Probability</h4>
  <div style="display:flex;align-items:center"><div style="width:20px;height:10px;background:#0000FF;margin-right:6px"></div>Low (≤ 0.2)</div>
  <div style="display:flex;align-items:center"><div style="width:20px;height:10px;background:#00FFFF;margin-right:6px"></div>Moderate (≤ 0.4)</div>
  <div style="display:flex;align-items:center"><div style="width:20px;height:10px;background:#FFFF00;margin-right:6px"></div>Elevated (≤ 0.6)</div>
  <div style="display:flex;align-items:center"><div style="width:20px;height:10px;background:#FFA500;margin-right:6px"></div>High (≤ 0.8)</div>
  <div style="display:flex;align-items:center"><div style="width:20px;height:10px;background:#FF0000;margin-right:6px"></div>Critical (> 0.8)</div>
`;

document.body.appendChild(legend);

