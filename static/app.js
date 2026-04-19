document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        renderDashboard(data);
    } catch (error) {
        console.error("Error fetching data:", error);
        document.getElementById('indices-container').innerHTML = '<div class="loader">데이터를 불러오는 중 오류가 발생했습니다.</div>';
        document.getElementById('sectors-container').innerHTML = '<div class="loader">데이터를 불러오는 중 오류가 발생했습니다.</div>';
    }
}

function renderDashboard(data) {
    const indicesContainer = document.getElementById('indices-container');
    const sectorsContainer = document.getElementById('sectors-container');

    // 1. Calculate global max and min for the dynamic heatmap
    let allValues = [];
    
    // Add indices
    data.indices.forEach(item => allValues.push(item.change));
    
    // Add sectors and themes
    data.sectors.forEach(sector => {
        allValues.push(sector.change);
        sector.themes.forEach(theme => allValues.push(theme.change));
    });

    // Remove NaN or undefined just in case
    allValues = allValues.filter(val => typeof val === 'number' && !isNaN(val));

    const maxVal = Math.max(...allValues, 0.01); // Avoid division by zero
    const minVal = Math.min(...allValues, -0.01);

    // Color Assignment Logic
    const getHeatmapClass = (val) => {
        if (val > 0) {
            if (val >= maxVal * 0.66) return 'pos-3';
            if (val >= maxVal * 0.33) return 'pos-2';
            return 'pos-1';
        } else if (val < 0) {
            if (val <= minVal * 0.66) return 'neg-3';
            if (val <= minVal * 0.33) return 'neg-2';
            return 'neg-1';
        } else {
            return 'neu';
        }
    };

    // Render Indices
    indicesContainer.innerHTML = '';
    data.indices.forEach(obj => {
        const div = document.createElement('div');
        div.className = `card ${getHeatmapClass(obj.change)}`;
        div.innerHTML = `
            <div class="card-title">${obj.name}</div>
            <div class="card-value">${obj.change > 0 ? '+' : ''}${obj.change.toFixed(2)}%</div>
        `;
        indicesContainer.appendChild(div);
    });

    // Render Sectors & Themes (Board Layout)
    cachedSectors = data.sectors;
    renderSectors();
}

let currentSort = 'desc'; // 'desc', 'asc', 'name'
let currentView = 'all';  // 'all', 'compact'
let cachedSectors = [];

function renderSectors() {
    const boardCols = [
        document.getElementById('board-col-1'),
        document.getElementById('board-col-2'),
        document.getElementById('board-col-3'),
        document.getElementById('board-col-4'),
        document.getElementById('board-col-5')
    ];
    boardCols.forEach(col => col.innerHTML = '');

    let sectorsToRender = [...cachedSectors];

    // Apply User Sort
    if (currentSort === 'desc') {
        sectorsToRender.sort((a, b) => b.change - a.change);
    } else if (currentSort === 'asc') {
        sectorsToRender.sort((a, b) => a.change - b.change);
    } else {
        sectorsToRender.sort((a, b) => a.name.localeCompare(b.name, 'ko'));
    }

    sectorsToRender.forEach((sector, i) => {
        const table = document.createElement('table');
        table.className = 'sector-table';
        
        // Header
        const headerRow = document.createElement('tr');
        const th = document.createElement('th');
        th.colSpan = 2;
        const sIcon = sector.change > 0 ? '▲' : (sector.change < 0 ? '▼' : '');
        th.innerHTML = `${sector.name} <span style="font-size:0.85rem; margin-left:8px; font-weight:normal;">${sIcon} ${sector.change > 0 ? '+' : ''}${sector.change.toFixed(2)}%</span>`;
        if (sector.change > 0) th.style.color = '#000'; // Kept original style, adjust if needed
        headerRow.appendChild(th);
        table.appendChild(headerRow);
        
        // Themes Truncation (Max 3, prioritized by most extreme moves)
        let themesToRender = sector.themes;
        if (currentView === 'compact' && themesToRender.length > 3) {
            let topMovers = [...themesToRender].sort((a, b) => Math.abs(b.change) - Math.abs(a.change)).slice(0, 3);
            topMovers.sort((a, b) => b.change - a.change); // Re-sort for display (Highest to Lowest)
            themesToRender = topMovers;
        }

        themesToRender.forEach(theme => {
            const tr = document.createElement('tr');
            
            const icon = theme.change > 0 ? '▲ ' : (theme.change < 0 ? '▼ ' : '');
            
            // Standard Text Colors (Name is default black/dark, Value is colored)
            let nameClass = 'text-neu'; // name is mostly dark
            let valClass = theme.change > 0 ? 'text-pos' : (theme.change < 0 ? 'text-neg' : 'text-neu');
            
            // Strong Highlight Rules ( >= 3% or <= -3% )
            if (theme.change >= 3) {
                nameClass = 'bg-pos-strong';
                valClass = 'bg-pos-strong';
            } else if (theme.change <= -3) {
                nameClass = 'bg-neg-strong';
                valClass = 'bg-neg-strong';
            }
            
            const nameTd = document.createElement('td');
            nameTd.className = `theme-name ${nameClass}`;
            nameTd.textContent = icon + theme.name;
            
            const valTd = document.createElement('td');
            valTd.className = `theme-val ${valClass}`;
            valTd.textContent = `${theme.change > 0 ? '+' : ''}${theme.change.toFixed(2)}%`;
            
            tr.appendChild(nameTd);
            tr.appendChild(valTd);
            table.appendChild(tr);
        });

        // Distribute tables across the columns
        boardCols[i % 5].appendChild(table);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const sortBtn = document.getElementById('sort-btn');
    if (sortBtn) {
        sortBtn.addEventListener('click', () => {
            if (currentSort === 'desc') {
                currentSort = 'asc';
                sortBtn.textContent = '정렬: 낮은 ⬇️';
            } else if (currentSort === 'asc') {
                currentSort = 'name';
                sortBtn.textContent = '정렬: 이름 🔠';
            } else {
                currentSort = 'desc';
                sortBtn.textContent = '정렬: 높은 ⬆️';
            }
            if (cachedSectors.length > 0) renderSectors();
        });
    }

    const filterBtn = document.getElementById('filter-btn');
    if (filterBtn) {
        filterBtn.addEventListener('click', () => {
            if (currentView === 'all') {
                currentView = 'compact';
                filterBtn.textContent = '보기: 하위 3개 요약 ✂️';
            } else {
                currentView = 'all';
                filterBtn.textContent = '보기: 전체 뷰 📋';
            }
            if (cachedSectors.length > 0) renderSectors();
        });
    }
});
