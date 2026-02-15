const CURSOR_KEYS = [
    "Arrow","Help","AppStarting","Wait","Crosshair",
    "IBeam","Handwriting","No","SizeNS","SizeWE",
    "SizeNWSE","SizeNESW","SizeAll","Hand","UpArrow"
];

const DEFAULT_IMAGES = {
    Arrow:        "image/aero_arrow.png",
    Help:         "image/aero_helpsel.png",
    AppStarting:  "image/aero_working_xl.png",
    Wait:         "image/aero_busy_xl.png",
    Crosshair:    "image/cross_il.png",
    IBeam:        "image/beam_rl.png",
    Handwriting: "image/aero_pen.png",
    No:           "image/aero_unavail.png",
    SizeNS:       "image/aero_ns.png",
    SizeWE:       "image/aero_ew.png",
    SizeNWSE:     "image/aero_nwse.png",
    SizeNESW:     "image/aero_nesw.png",
    SizeAll:      "image/aero_move.png",
    Hand:         "image/aero_link.png",
    UpArrow:      "image/aero_up.png",
};

let currentOriginalGroup = null;

window.addEventListener('pywebviewready', async () => {
    renderRows();
    await refreshGroups();
});

function renderRows() {
    const container = document.getElementById('cursorList');
    container.innerHTML = CURSOR_KEYS.map(k => `
        <div class="position-row">
            <div class="thumb-preview" id="prev-${k}">
                <img src="${DEFAULT_IMAGES[k]}">
            </div>
            <input id="input-${k}" class="position-input" readonly placeholder="${k}">
            <button class="browse-button" onclick="handleBrowse('${k}')">浏览</button>
        </div>
    `).join('');
}

async function refreshGroups() {
    const groups = await pywebview.api.get_existing_groups();
    const dropdown = document.getElementById('groupDropdown');
    dropdown.innerHTML = '';

    const newOpt = document.createElement('div');
    newOpt.className = 'dropdown-option';
    newOpt.innerText = '新建鼠标组';
    newOpt.onclick = () => selectGroup(null);
    dropdown.appendChild(newOpt);

    groups.forEach(g => {
        const opt = document.createElement('div');
        opt.className = 'dropdown-option';
        opt.innerText = g;
        opt.onclick = () => selectGroup(g);
        dropdown.appendChild(opt);
    });
}

async function selectGroup(name) {
    currentOriginalGroup = name;
    document.getElementById('groupDropdown').style.display = 'none';

    const input = document.getElementById('groupNameInput');

    CURSOR_KEYS.forEach(k => {
        document.getElementById(`input-${k}`).value = '';
        document.getElementById(`prev-${k}`).innerHTML =
            `<img src="${DEFAULT_IMAGES[k]}">`;
    });

    if (!name) {
        input.value = '';
        input.placeholder = '请输入新组名';
        return;
    }

    input.value = name;
    const data = await pywebview.api.load_group_config(name);

    for (const k of CURSOR_KEYS) {
        if (data[k]) {
            document.getElementById(`input-${k}`).value = data[k];
            updatePreview(k, data[k]);
        }
    }
}

async function handleBrowse(key) {
    const path = await pywebview.api.open_file_dialog();
    if (!path) return;
    document.getElementById(`input-${key}`).value = path;
    updatePreview(key, path);
}

async function updatePreview(key, path) {
    const b64 = await pywebview.api.get_preview_base64(path);
    if (b64) {
        document.getElementById(`prev-${key}`).innerHTML =
            `<img src="${b64}">`;
    }
}

async function saveData() {
    const name = document.getElementById('groupNameInput').value.trim();
    if (!name) return alert("请输入组名");

    const data = {};
    CURSOR_KEYS.forEach(k => {
        data[k] = document.getElementById(`input-${k}`).value;
    });

    const res = await pywebview.api.save_group_config(
        name, data, currentOriginalGroup
    );
    alert(res.msg);
    await refreshGroups();
    currentOriginalGroup = name;
}

function showDropdown() {
    document.getElementById('groupDropdown').style.display = 'block';
}

document.addEventListener('click', e => {
    if (!e.target.closest('.header-row')) {
        document.getElementById('groupDropdown').style.display = 'none';
    }
});
