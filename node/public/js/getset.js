const _FEATURES = [
    'kategori', 'underkategori',
    'land', 'distrikt', 'underdistrikt',
    'volum',
    'butikk',
    'årgang', 'beskrivelse.kort', 'passer til', 'kork', 'lagring'
];
const _DIVIDER = [' ', 'UTILGJENGELIGE VALG', '-------------------'];
let _FOCUS = null;

async function initialise(state) {
    let uniquesData = await uniques(_FEATURES);
    for (let [feature, values] of Object.entries(uniquesData)) {
        let items = {};
        for (let k of values.sort()) {
            if (k && k !== '-') items[k.toString()] = k;
        }
        state['dropdown'][feature] = items;
        state['dropdown']['full'][feature] = Object.keys(items);
    }

    // Convert volume to neatly formatted string.
    for (let [vol, value] of Object.entries(state['dropdown']['volum'])) {
        state['dropdown']['volum'][vol] = `${parseFloat(value)} cL`;
    }
    for (let [year, value] of Object.entries(state['dropdown']['argang'])) {
        state['dropdown']['argang'][year] = `${parseFloat(value)}`;
    }

    await set_data(state);
}

async function set_data(state, fresh = true) {
    state['flag']['updating'] = true;

    // Toggle inclusion of alcohol-free products if this category is chosen.
    if (state['valgt']['kategori'].includes('Alkoholfritt')) {
        state['valgt']['alkoholfritt'] = ['True'];
    }

    // Removing the divider from the selection.
    for (let [feature, values] of Object.entries(state['valgt'])) {
        if (!['fra', 'til', 'alkohol'].includes(feature)) {
            state['valgt'][feature] = values.filter(v => !_DIVIDER.includes(v));
        }
    }
    let focus = state['data']['fokus'] ? state['data']['fokus'] : 'prisendring';

    // Loading data for the current selection.
    try {
        let [data, total] = await load(
            ...state['valgt'],

            sorting=focus,
            ascending=focus !== 'ny' ? state['data']['stigende'].length > 0 : state['data']['stigende'].length <= 0,
            amount=state['data']['antall'],
            page=state['side']['gjeldende'],

            search=state['finn']['navn'],
            filters=state['finn']['navn'] ? state['finn']['filter'] : true,

            fresh=fresh,
        );
        state['flag']['invalid'] = false;
        state['flag']['valid'] = true;

        // Remove duplicates if any.
        // TODO: Remove duplicates in JavaScript.

        // Setting the discount data for the current selection.
        _discounts(state, data);

        // Setting the total number {
            state['side']['totalt'] = Math.max(Math.floor(total / state['data']['antall']), 1);
            state['side']['gjeldende'] = 1;
        }
    } catch (error) {
        state['flag']['updating'] = false;
        state['flag']['invalid'] = true;
        state['flag']['valid'] = false;
        return;
    }

    state['flag']['updating'] = false;
}

async function set_focus(state) {
    if (_FOCUS === state['data']['fokus']) {
        await set_data(state);
        return;
    }

    state['valgt']['fra'] = null;
    state['valgt']['til'] = null;
    if (!['navn', 'ny'].includes(state['data']['fokus'])) {
        state['flag']['mellom'] = true;
    } else {
        state['flag']['mellom'] = false;
    }

    _FOCUS = state['data']['fokus'];
    await set_data(state);
}

async function set_next_page(state) {
    if (state['side']['gjeldende'] >= state['side']['totalt']) {
        return;
    }

    state['side']['gjeldende'] += 1;

    await set_data(state, false);
}

async function set_previous_page(state) {
    if (state['side']['gjeldende'] < 2) {
        return;
    }

    state['side']['gjeldende'] -= 1;

    await set_data(state, false);
}

async function set_page_one(state) {
    state['side']['gjeldende'] = 1;
    await set_data(state, false);
}

async function set_page(state) {
    await set_data(state, false);
}

async function _dropdown(state, feature, omit = [], include_all = false) {
    // Get the possible values for the current selection.
    // Omitting the current feature and the ones in the omit list.
    let possible = await uniques(
        [feature],
        ...Object.fromEntries(Object.entries(state['valgt']).filter(([k, v]) => ![...omit, feature].includes(k))),
    )[feature];

    // Get the values that are not possible.
    let others = include_all ? [...new Set(state['dropdown']['full'][feature]).difference(new Set(possible))] : [];

    // Toggle flag if possible values, and a flag exists.
    if (state['flag'][feature] !== undefined) {
        state['flag'][feature] = possible.length > 0;
    }

    // Update the dropdown for the current feature.
    // Including impossible values if `include_all` is `True`.
    let dropdown = {};
    for (let cat of [...possible, ...(_DIVIDER if others else []), ...others].sort()) {
        dropdown[cat.toString()] = feature !== 'volum' && feature !== 'argang' ? cat : `${parseFloat(cat)} cL`;
    }
    state['dropdown'][feature] = dropdown;

    // Remove already selected values if they are not in the possible's list.
    for (let choice of state['valgt'][feature].map(c => feature === 'volum' ? parseFloat(c) : c)) {
        if (!possible.includes(choice)) {
            state['valgt'][feature] = state['valgt'][feature].filter(c => c !== choice);
        }
    }
}

async function set_store(state) {
    if (state['valgt']['butikk'].length > 0) {
        state['flag']['butikk'] = true;
    } else {
        state['flag']['butikk'] = false;
    }

    await set_category(state, false);
    await set_country(state, false);
    await set_volume(state, false);
    await set_data(state);
}

async function set_category(state, main = true) {
    if (state['valgt']['kategori'].length === 0) {
        state['flag']['underkategori'] = false;
        state['valgt']['underkategori'] = [];
    } else {
        await _dropdown(state, 'underkategori');
    }

    // Cascade downwards.
    await set_subcategory(state, main);
}

async function set_subcategory(state, main = true) {
    if (!main) {
        return;
    }

    await _dropdown(state, 'land', ['distrikt', 'underdistrikt'], true);
    await _dropdown(state, 'volum', [], true);

    await set_country(state, false);
    await set_volume(state, false);

    await set_data(state);
}

async function set_country(state, main = true) {
    if (state['valgt']['land'].length === 0) {
        state['flag']['distrikt'] = false;
        state['flag']['underdistrikt'] = false;
        state['valgt']['distrikt'] = [];
        state['valgt']['underdistrikt'] = [];
    } else {
        await _dropdown(state, 'distrikt', ['underdistrikt']);
    }

    // Cascade downwards.
    await set_district(state, main);
}

async function set_district(state, main = true) {
    if (state['valgt']['distrikt'].length === 0) {
        state['flag']['underdistrikt'] = false;
        state['valgt']['underdistrikt'] = [];
    } else {
        await _dropdown(state, 'underdistrikt');
    }

    // Cascade downwards.
    await set_subdistrict(state, main);
}

async function set_subdistrict(state, main = true) {
    if (!main) {
        return;
    }

    await _dropdown(state, 'kategori', ['underkategori'], true);
    await _dropdown(state, 'volum', [], true);

    await set_category(state, false);
    await set_volume(state, false);

    await set_data(state);
}

async function set_volume(state, main = true) {
    if (!main) {
        return;
    }

    await _dropdown(state, 'kategori', ['underkategori'], true);
    await _dropdown(state, 'land', ['distrikt', 'underdistrikt'], true);

    await set_category(state, false);
    await set_country(state, false);

    await set_data(state);
}

async function reset_selection(state) {
    for (let feature of Object.keys(state['valgt'])) {
        state['valgt'][feature] = feature !== 'fra' && feature !== 'til' && feature !== 'alkohol' ? [] : null;
    }

    // Reset the dropdown.
    // Arbitrarily chosen, as all `set_{selection}` functions cascade downwards.
    await _dropdown(state, 'kategori');
    await set_category(state);
}

function _discounts(state, data) {
    // Updates the discount data in the state to correspond with the current selection.

    // TODO: Implement this function in JavaScript.
}

// TODO: Implement the `graph` function in JavaScript.
